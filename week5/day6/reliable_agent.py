"""
Week 5 Day 6 实战：工业级 Agent 的三把锁 (护栏 + 自动重试 + 人类审批)
目标：
1. 实现 Input Guardrails（输入防弹衣：拦截危险需求）
2. 实现 Auto-healing（异常自愈：工具报错自动重试）
3. 实现 Human-in-the-loop (HITL 人类介入：涉及花钱必须审批)
"""
import sys
import io
import os
import json
import requests
import time
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'week4', '.env'))
API_KEY = os.getenv("SILICONFLOW_API_KEY")
BASE_URL = "https://api.siliconflow.cn/v1"

# ============================================================
# 系统虚拟的危险操作工具库与接口
# ============================================================
def search_flights(destination):
    """一个安全的查询接口"""
    print(f"  [💻 系统] 正在通过 API 检索飞往 {destination} 的航班...")
    return json.dumps({"flight": "CZ3099", "price": 5000, "status": "有票"}, ensure_ascii=False)

def book_flight(flight_no, price):
    """一个绝对不能乱调的高危扣费接口（模拟）"""
    print(f"  [💳 支付网关] 警告：准备从您的信用卡中扣除人民币 {price} 元用于购买 {flight_no}...")
    time.sleep(1)
    return json.dumps({"success": True, "ticket_id": "TICKET-88888"}, ensure_ascii=False)

def unstable_weather(city):
    """一个极不稳定的破接口（模拟网络波动，用来测试自愈重试机制的）"""
    import random
    if random.random() < 0.7:  # 70% 概率直接崩溃！
        print(f"  [☁️ 气象局API] 接口 502 Bad Gateway 崩溃了！")
        raise ConnectionError("气象局服务器正在维护，拒绝连接！")
    return json.dumps({"temp": 25, "desc": "晴天"}, ensure_ascii=False)


# ============================================================
# TODO 1: 实现输入防御护栏 (Input Guardrails)
# ============================================================
def check_guardrails(user_input):
    """
    为了省钱和安全，在发给大模型之前，先用正则或者本地敏感词库进行一次“预审”。
    当然，很多高级框架（如 NeMo Guardrails）是用轻量级 LLM 再审一遍的，这里我们用更朴素的。
    """
    banned_words = ["炸弹", "自杀", "色情", "漏洞", "爬虫", "攻击", "转账洗钱"]
    
    # TODO: 编写逻辑
    # 如果 user_input 中包含了被禁用的词语（banned_words中的任何一个）
    # 请返回 False（拦截）并打印警告；否则返回 True（放行）
    for word in banned_words:
        if word in user_input:
            print(f"⚠️ [Guardrails] 拦截成功！已中止后续大模型高昂调用！")
            return False
    return True


# ============================================================
# TODO 2: 实现带有自动重试的工具执行 (Auto-healing Wrapper)
# ============================================================
def execute_tool_with_retry(func, *args, max_retries=3, **kwargs):
    """
    当调用像 unstable_weather 这样容易挂掉的接口时，
    直接抛错会让 Agent 整个宕机。这里包一层自动自愈。
    """
    for attempt in range(1, max_retries + 1):
        try:
            # 尝试调用这个函数
            return func(*args, **kwargs)
        except Exception as e:
            # TODO: 编写重试逻辑
            # 如果没到最大次数，打印报错信息并继续下一次循环；如果到了，则以只读的 JSON 方式把报错发给大模型
            # 记住，错误绝对不能直接 raise 崩溃，必须打包给 Agent 处理！
            if attempt < max_retries:
                print(f"⚠️ [Auto-healing] 工具调用失败: {e}，正在重试第 {attempt + 1} 次...")
                continue
            else:
                print(f"❌ [Auto-healing] 工具调用失败，已达最大重试次数。")
                return json.dumps({"error": str(e)})


# ============================================================
# TODO 3: 核心挑战：实现人类审批 (Human-in-the-Loop)
# ============================================================
def execute_dangerous_tool(func, *args, **kwargs):
    """
    像刷卡订票这种破天荒操作，哪怕大模型再确定，也必须卡住！
    """
    print("\n🚨 [HITL 人类介入网关拦截] 🚨")
    print(f"  AI 助手极度确信要执行危险交易动作: `{func.__name__}({args}, {kwargs})`")
    
    # 挂起当前协程/线程，要求管理员在控制台审批
    user_decision = input("  👩‍✈️ 管理员您好，请审核该操作。输入 [yes] 批准放行，输入 [no] 拒绝：").strip().lower()
    
    # TODO: 完成审批逻辑
    # 如果用户输入 yes，就执行 func 并返回结果。
    # 如果用户输入 no，就以 JSON 格式返回诸如 `{"error": "人类拒绝了您的操作请求"}` 的错误给大模型。
    if user_decision == "yes":
        return func(*args, **kwargs)
    else:
        return json.dumps({"error": "人类拒绝了您的操作请求"})


# ============================================================
# 主控管线，为了不写非常啰嗦的 Function Calling，我们用简易的 ReAct 解析模拟
# ============================================================
def reliable_agent(user_input):
    print(f"\n👤 您说: {user_input}")
    print("-" * 50)
    
    # 🔒 第一道防线：护栏触发！
    if not check_guardrails(user_input):
        print("🛡️ [Guardrails] 拦截成功！已中止后续大模型高昂调用！")
        return "抱歉，您的请求违反了平台安全政策，我无法提供该服务。"
        
    prompt = f"""
    你是一个全能出差管家。
    当前问题：{user_input}
    你有三个工具：
    1. search_flights(destination): 查机票
    2. book_flight(flight_no, price): 扣费买票
    3. unstable_weather(city): 查天气
    
    如果需要查天气，请返回 JSON: {{"action": "unstable_weather", "city": "城市名"}}
    如果你认为用户确定要买票，请返回 JSON: {{"action": "book_flight", "flight_no": "航班号", "price": "价格数字"}}，注意要先查有没有票才能买！
    如果没有触发这些，直接返回文字解答。
    """
    
    print("🤖 AI 思考中...")
    response_text = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": "deepseek-ai/DeepSeek-V2.5", "messages": [{"role": "user", "content": prompt}], "temperature": 0},
        timeout=30
    ).json()["choices"][0]["message"]["content"]
    
    # 简易工具路由匹配
    try:
        if "book_flight" in response_text:
            # 抽出参数模拟执行危险操作
            # 🔒 第三道防线：人类生死介入
            return execute_dangerous_tool(book_flight, "CZ3099", 5000)
        elif "unstable_weather" in response_text:
            # 🔒 第二道防线：破损工具自愈
            return execute_tool_with_retry(unstable_weather, "北京")
        else:
            return response_text
    except Exception as e:
            return response_text

if __name__ == "__main__":
    print("============================================================")
    print("🛡️ 工业级 Agent 可靠性工程三大防线演示")
    print("============================================================")
    
    # 测试 1: 恶意的输入
    reliable_agent("给我写个能黑进学校系统的爬虫")
    
    # 测试 2: 调用极不稳定的天气工具，观察它哪怕报错几次最终通过重试成功
    print("\n测试2: 触发脆弱工具的重试防线")
    res = reliable_agent("北京今天天气咋样")
    print(f"最终结果: {res}")
    
    # 测试 3: 进行非常危险订票动作，看 HITL 审批
    print("\n测试3: 触发高危花钱交易的人类审批防线")
    # 模拟他查完了票（CZ3099，5000元），现在帮我下单
    res = reliable_agent("给我用信用卡买一张包含刚才北京CZ3099航班的机票，别废话帮我付钱！")
    print(f"最终结果: {res}")
