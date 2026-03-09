"""
Week 5 Day 1 实战：手写 ReAct Agent
目标：理解 Agent 的 Thought → Action → Observation 循环
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
# 工具定义（Agent 可以使用的工具）
# ============================================================
def tool_calculator(expression):
    """计算器工具：计算数学表达式"""
    try:
        result = eval(expression)
        return f"计算结果: {expression} = {result}"
    except:
        return f"计算错误: 无法计算 {expression}"


def tool_lookup(keyword):
    """知识库查询工具：查询公司政策"""
    knowledge = {
        "年假": "入职满1年享有15天年假，满5年享有20天。",
        "加班": "工作日加班按1.5倍工资，周末2倍，法定节假日3倍。",
        "试用期": "试用期3个月，工资为正式的80%。",
        "培训": "每年每人5000元培训基金，凭结业证书报销。",
        "报销": "费用发生30天内提交，500以下部门经理审批，500以上总监审批。",
    }
    for key, value in knowledge.items():
        if key in keyword:
            return f"查询结果: {value}"
    return f"未找到关于'{keyword}'的信息"


# 工具注册表
TOOLS = {
    "calculator": {"func": tool_calculator, "desc": "计算数学表达式，参数为数学表达式字符串"},
    "lookup": {"func": tool_lookup, "desc": "查询公司政策信息，参数为查询关键词"},
}


# ============================================================
# TODO 1: 实现 Agent 决策函数
# ============================================================
def agent_decide(question, history):
    """
    让 LLM 决定下一步动作
    返回: {"thought": "...", "action": "工具名", "action_input": "参数"}
    或:   {"thought": "...", "action": "finish", "action_input": "最终回答"}
    
    TODO: 设计一个 prompt，让 LLM 按 ReAct 格式输出决策
    提示：
    - 告诉 LLM 可用的工具列表和描述
    - 把对话历史 history 加入 prompt
    - 要求 LLM 用 JSON 格式返回 thought/action/action_input
    """
    tools_desc = "\n".join([f"- {name}: {info['desc']}" for name, info in TOOLS.items()])
    
    prompt = f"""你是一个 ReAct Agent，通过 Thought→Action→Observation 循环解决问题。

    可用工具：
    {tools_desc}

    对话历史：
    {json.dumps(history, ensure_ascii=False) if history else '无'}

    当前问题：{question}

    请用 JSON 格式输出你的决策，格式如下：
    {{"thought": "你的思考", "action": "工具名或finish", "action_input": "参数或最终回答"}}

    规则：
    - 需要查资料用 lookup，需要计算用 calculator
    - 如果已有足够信息回答问题，设 action="finish"，action_input=最终回答
    - 只输出 JSON，不要其他内容
    """

    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-ai/DeepSeek-V2.5",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 300
        },
        timeout=30
    )
    content = resp.json()["choices"][0]["message"]["content"].strip()
    
    # 解析 JSON 响应
    try:
        # 提取 JSON 部分（LLM 可能输出多余文字）
        start = content.find("{")
        end = content.rfind("}") + 1
        return json.loads(content[start:end])
    except:
        return {"thought": content, "action": "finish", "action_input": content}


# ============================================================
# TODO 2: 实现 ReAct 循环
# ============================================================
def react_agent(question, max_steps=5):
    """
    ReAct Agent 主循环：
    1. 调用 agent_decide 获取决策
    2. 如果 action == "finish" → 返回最终答案
    3. 否则 → 执行工具 → 记录 Observation → 继续循环
    4. 最多循环 max_steps 次（防止死循环）
    
    TODO: 实现循环逻辑
    提示：
    - 用 history 列表记录每一步的 thought/action/observation
    - 每次循环打印当前步骤信息
    """
    history = []
    for i in range(max_steps):
        decision = agent_decide(question, history)
        print(f"Step {i+1}: {decision}")
        if decision["action"] == "finish":
            return decision["action_input"]
        elif decision["action"] in TOOLS:
            tool = TOOLS[decision["action"]]
            obs = tool["func"](decision["action_input"])
            history.append({"thought": decision["thought"], "action": decision["action"], "action_input": decision["action_input"], "observation": obs})
            print(f"  🔍 Observation: {obs}")
    return "达到最大步数限制，无法完成任务"
        


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ReAct Agent 测试")
    print("=" * 60)
    
    questions = [
        "公司年假政策是什么？",
        "一个月加班 20 小时，按 1.5 倍算，底薪 50 元/小时，加班费多少？",
        "试用期工资打几折？如果正式工资 10000，试用期拿多少？",
    ]
    
    for q in questions:
        print(f"\n❓ {q}")
        answer = react_agent(q)
        print(f"\n💡 最终回答: {answer}")
        print("-" * 40)
