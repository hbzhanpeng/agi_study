"""
Week 5 Day 2 深度实战：带记忆的对话 Agent
目标：组合 Chain + Memory + Tool，构建一个真正的多轮对话 Agent
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
# 基础组件（复用 mini_langchain）
# ============================================================
class LLM:
    def call(self, prompt):
        resp = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-ai/DeepSeek-V2.5",
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0, "max_tokens": 300},
            timeout=30
        )
        return resp.json()["choices"][0]["message"]["content"].strip()


class Memory:
    def __init__(self):
        self.messages = []
    
    def add(self, role, content):
        self.messages.append({"role": role, "content": content})
    
    def get_context(self):
        if not self.messages:
            return "无历史对话"
        return "\n".join([f"{m['role']}: {m['content']}" for m in self.messages[-6:]])


# 工具定义
TOOLS = {
    "lookup": {
        "desc": "查询公司政策信息，参数为查询关键词",
        "func": lambda kw: next(
            (v for k, v in {
                "年假": "入职满1年享有15天，满5年享有20天。需提前3天申请。",
                "加班": "工作日1.5倍，周末2倍，法定节假日3倍。每日不超过3小时。",
                "试用期": "试用期3个月，工资为正式的80%。不享有年假和远程办公。",
                "培训": "每年每人5000元培训基金，凭结业证书报销。",
                "报销": "30天内提交，500以下经理审批，500以上总监审批。",
                "远程": "每周最多2天，提前1天申请。试用期不可申请。",
                "晋升": "每半年绩效评估，连续两次A可晋升，连续两次D进入改进计划。",
            }.items() if k in kw),
            f"未找到关于'{kw}'的信息"
        )
    },
    "calculator": {
        "desc": "计算数学表达式，参数为表达式字符串",
        "func": lambda expr: str(eval(expr))
    }
}


# ============================================================
# TODO 1: 实现带记忆的路由决策
# ============================================================
def decide_with_memory(llm, question, memory, working_memory=None):
    """带记忆的决策：长期记忆 + 短期工具结果"""
    tools_desc = "\n".join([f"- {k}: {v['desc']}" for k, v in TOOLS.items()])
    history = memory.get_context()
    
    # 短期记忆：当前任务的工具调用结果
    tool_results = ""
    if working_memory:
        tool_results = "\n已获取的信息：\n" + "\n".join(
            [f"  [{w['tool']}] {w['input']} → {w['result']}" for w in working_memory]
        )
    
    prompt = f"""你是一个智能 HR 助手。根据对话历史和已获取的信息来回答问题。

    对话历史：
    {history}
    {tool_results}

    当前问题：{question}

    可用工具：
    {tools_desc}

    规则：
    - 如果对话历史或已获取的信息中已有足够信息，直接 action="finish"
    - 需要查公司政策用 lookup，需要计算用 calculator
    - 只返回 JSON，格式：{{"thought": "思考", "action": "工具名或finish", "action_input": "参数或最终答案"}}
    """
    
    content = llm.call(prompt)
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        return json.loads(content[start:end])
    except:
        return {"thought": content, "action": "finish", "action_input": content}


# ============================================================
# TODO 2: 实现多轮对话循环
# ============================================================
def chat_agent(llm, memory, question, max_steps=5):
    """
    多轮对话 Agent：
    1. 把用户问题记入 memory
    2. 执行 ReAct 循环
    3. 把最终回答也记入 memory
    
    TODO: 实现完整逻辑
    提示：
    - memory.add("user", question)  # 记录用户输入
    - 执行 ReAct 循环（复用 Day1 逻辑）
    - memory.add("assistant", answer)  # 记录 AI 回答
    - return answer
    """
    memory.add("user", question)
    working_memory = []  # 短期记忆：只在当前任务内有效
    for _ in range(max_steps):
        decision = decide_with_memory(llm, question, memory, working_memory)
        action = decision.get("action")
        action_input = decision.get("action_input", "")
        
        if action == "finish":
            memory.add("assistant", action_input)
            return action_input
        
        if action in TOOLS:
            result = TOOLS[action]["func"](action_input)
            # 工具结果只存短期记忆，不污染长期对话记忆！
            working_memory.append({"tool": action, "input": action_input, "result": result})
    
    # 兜底：防止死循环返回 None
    fallback = "抱歉，我暂时无法回答这个问题。"
    memory.add("assistant", fallback)
    return fallback


# ============================================================
# 测试：多轮对话
# ============================================================
if __name__ == "__main__":
    llm = LLM()
    memory = Memory()
    
    print("=" * 60)
    print("🤖 带记忆的多轮对话 Agent")
    print("=" * 60)
    
    # 模拟多轮对话 —— 关键看第3轮能否记住"小明"
    conversations = [
        "你好，我叫小明，我入职2年了",
        "我有多少天年假？",
        "我的名字是什么？入职几年了？",  # ← 考验记忆！
        "如果年假15天，每天工资500元，年假工资总共多少？",
        "培训基金有多少？我想报个课程",
    ]
    
    for q in conversations:
        print(f"\n👤 用户: {q}")
        answer = chat_agent(llm, memory, q)
        print(f"🤖 Agent: {answer}")
        print("-" * 40)
    
    print("\n📝 完整对话记忆:")
    print(memory.get_context())
