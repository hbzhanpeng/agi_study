"""
Week 5 Day 4 高阶实战：工业级复合记忆系统 & Multi-Query
目标：
1. 实现带有“滑动窗口”的短期 Buffer 记忆
2. 体验 Multi-Query（多路查询展开）技巧解决检索死角问题
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'week4', '.env'))
API_KEY = os.getenv("SILICONFLOW_API_KEY")
BASE_URL = "https://api.siliconflow.cn/v1"

# ============================================================
# 基础大模型调用封装
# ============================================================
def call_llm(prompt, temperature=0.1):
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-ai/DeepSeek-V2.5",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": 500
        },
        timeout=30
    )
    return resp.json()["choices"][0]["message"]["content"].strip()


# ============================================================
# 模块 1：短期滑动窗口记忆 (Sliding Window Buffer)
# ============================================================
class WindowMemory:
    """
    只管保留最近 N 轮的记忆，防止 Token 爆炸。
    """
    def __init__(self, max_turns=3):
        self.messages = []
        self.max_turns = max_turns * 2  # 一轮包含一问一答，所以 * 2
        
    def add(self, role, content):
        self.messages.append({"role": role, "content": content})
        # 只要超出限度，就切掉最旧的那句话（保证短平快）
        if len(self.messages) > self.max_turns:
            self.messages = self.messages[-self.max_turns:]
            
    def get_context(self):
        if not self.messages:
            return "无近期对话。"
        return "\n".join([f"{m['role']}: {m['content']}" for m in self.messages])

# ============================================================
# TODO 1: 实现 Multi-Query（多路查询扩写）
# ============================================================
def generate_multi_queries(original_query):
    """
    让 LLM 把用户的一句话，裂变成 3 句意思相近但用词不同的查询。
    目的是增加向量检索的命中率！
    
    TODO: 设计 prompt
    要求 LLM：
    1. 生成 3 个变体
    2. 以 JSON 数组格式返回，如：["变体1", "变体2", "变体3"]
    """
    prompt = f"""
    你是一个专业的知识库检索助手。
    用户的问题是：“{original_query}”。
    请你把这个问题进行“多路查询扩写”，生成 3 个意思相近但用词不同的查询。
    要求：
    1. 必须生成 3 个变体。
    2. 变体之间用逗号隔开。
    3. 以 JSON 数组格式返回，例如：["变体1", "变体2", "变体3"]
    """
    
    content = call_llm(prompt, temperature=0.7)  # 温度调高一点，增加发散性
    
    try:
        start = content.find("[")
        end = content.rfind("]") + 1
        return json.loads(content[start:end])
    except:
        return [original_query]


# 这是一个模拟的死板向量检索函数（如果没匹配到同义词就会搜不到）
def mock_vector_search(queries):
    knowledge_db = {
        "考勤打卡规范与异常处理": "员工需要在钉钉系统完成上下班打卡。漏打卡需提交补签流程。",
        "福利补贴报销指南": "打车发票需要在次月5号前贴票报销。",
        "网络安全红线": "严禁将公司源码上传至公共代码仓库如 Github。"
    }
    
    results = []
    # 只要任何一个变体命中了知识库的关键词，就算检索成功！
    for q in queries:
        for title, doc in knowledge_db.items():
            # 这是一个极度简化的关键词检索模拟（真实情况是算 embedding 的余弦相似度）
            if "考勤" in q or "打卡" in q:
                if doc not in results: results.append(doc)
            if "报销" in q or "发票" in q or "补贴" in q:
                if doc not in results: results.append(doc)
    return results


# ============================================================
# TODO 2: 实现记忆与 Multi-Query 融合的主管线
# ============================================================
def advanced_agent(window_memory, user_input):
    """
    高级记忆与检索流水线：
    1. 把用户的问题扩写出 3 个 Multi-Query 变体
    2. 把这 3 个变体扔进检索系统去查资料
    3. 把查到的资料 + Sliding Window 的近期对话记忆 + 原问题，一起给大模型回答
    4. 回答完后，更新滑动窗口记忆。
    """
    # 步骤 1: Multi-Query 扩写
    queries = generate_multi_queries(user_input)
    print(f"  [🔄 Multi-Query展开]: {queries}")
    
    # 步骤 2: 拿着一群小弟变体去库里搜
    retrieved_docs = mock_vector_search(queries)
    doc_context = "\n".join(retrieved_docs) if retrieved_docs else "未查找到相关资料。"
    print(f"  [📚 检索到的资料]: {doc_context}")
    
    # 获取近期的聊天对话记忆
    history_context = window_memory.get_context()
    
    # 步骤 3: 构造最终的 Prompt 发给模型
    # TODO: 编写 prompt，包含 history_context, doc_context, user_input
    final_prompt = f"""
    你是一个专业的知识库问答助手。
    
    【近期对话记忆】（用于理解上下文和指代）：
    {history_context}
    
    【检索到的知识库资料】：
    {doc_context}
    
    【当前用户问题】：
    {user_input}
    
    请根据以上信息，回答用户的问题。
    如果知识库中没有相关信息，请根据对话记忆回答，并提醒用户咨询人力资源部。
    """
    
    answer = call_llm(final_prompt)
    
    # 步骤 4: 更新短期记忆（为下一轮做好准备）
    window_memory.add("user", user_input)
    window_memory.add("assistant", answer)
    
    return answer


if __name__ == "__main__":
    print("============================================================")
    print("🧠 工业级复合记忆与 Multi-Query 实战")
    print("============================================================")
    
    memory = WindowMemory(max_turns=2)
    
    # -------- 第一轮对话 --------
    q1 = "我昨天忘签到了，怎么搞？"
    print(f"\n👤 用户: {q1}")
    # 注意：此时用户并没有提到“考勤”或者“打卡”，如果我们只搜“签到”，
    # 在死板的 `mock_vector_search` 里是搜不到 `考勤打卡规范` 的！
    # 但一旦有了 Multi-Query……大模型可能会把它扩写成包含“打卡”的变体。
    
    ans1 = advanced_agent(memory, q1)
    print(f"\n🤖 Agent: {ans1}\n")
    
    # -------- 第二轮对话（测试滑动窗口指代） --------
    q2 = "那如果我是车费发票呢？"
    print(f"\n👤 用户: {q2}")
    # 这里考察短期记忆：它必须记得前面讨论的是“怎么搞（处理流程）”
    
    ans2 = advanced_agent(memory, q2)
    print(f"\n🤖 Agent: {ans2}\n")
    
    # 查看窗口中到底存了什么
    print("============================================================")
    print("💡 当前短平快的 Sliding Window 记忆 (最多2轮, 4条)：")
    print("============================================================")
    print(memory.get_context())
