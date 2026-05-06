# multi_agent.py
import json
import requests
from rag import ask, add_note, call_llm_stream
from config import API_KEY, LLM_BASE_URL, CHAT_MODEL
from agent import run_agent

# 1. 定义各个子Agent
# ===== 子Agent定义 =====
agents_registry = [
    {
        "name": "rag_agent",
        "description": "负责查询知识库，回答用户的技术问题、踩坑经验",
    },
    {
        "name": "note_agent",
        "description": "负责把用户说的笔记、经验存入知识库",
    }
]
# 2. 定义协调Agent（Orchestrator）
# 3. Orchestrator判断意图 → 路由到对应Agent
# 4. 子Agent执行 → 返回结果

def split_questions(user_input: str) -> list:
    """用LLM把复杂问题拆分成子问题列表"""
    resp = requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": CHAT_MODEL,
            "messages": [
                {"role": "system", "content": (
                    "你是一个问题拆分助手。"
                    "将用户的问题拆分成多个独立的子问题。"
                    "只输出JSON数组，不要输出其他内容。"
                    "例如：[\"问题1\", \"问题2\"]"
                )},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0,
            "max_tokens": 200,
        },
        timeout=120
    )
    content = resp.json()["choices"][0]["message"]["content"]
    try:
        questions = json.loads(content)
        return questions if isinstance(questions, list) else [user_input]
    except:
        return [user_input]  # 解析失败就当作单个问题处理

# ===== 子Agent实现 =====
def rag_agent(user_input: str) -> str:
    # 第一步：拆分问题
    questions = split_questions(user_input)
    print(f"[rag_agent] 拆分成{len(questions)}个子问题: {questions}")
    
    # 第二步：对每个子问题分别检索
    all_results = []
    for q in questions:
        result  = run_agent(q)
        all_results.append(f"【子问题】{q}\n【答案】{result}")
    
    # 第三步：合并结果
    return "\n\n".join(all_results)

def note_agent(user_input: str) -> str:
    result = add_note(user_input)
    return result

def call_llm_with_agents(agents_registry: list, history: list = None) -> dict:
    if history is None:
        history = []
        
    messages = list(history)

    tools = [
        {
            "type": "function",
            "function": {
                "name": agent["name"],
                "description": agent["description"],
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "传给这个Agent的内容"
                        }
                    },
                    "required": ["input"]
                }
            }
        }
        for agent in agents_registry
    ]
        
    resp = requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": CHAT_MODEL,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 500,
            "tools": tools  # ← 还是tools字段
        },
        timeout=120
    )
    return resp.json()["choices"][0]["message"]

# ===== 协调Agent =====
def orchestrator(user_input: str) -> str:
    history = [
        {"role": "system", "content": (
            "你是一个路由助手，你只能调用工具，不能直接回答任何问题。"
            "用户问技术问题 → 必须调用rag_agent。"
            "用户要存笔记 → 必须调用note_agent。"
            "禁止直接回答，必须通过工具。"
        )},
        {"role": "user", "content": user_input}
    ]
    max_steps = 5  # 最多5步，防止死循环
    for step in range(max_steps):

        message = call_llm_with_agents(agents_registry, history)
        
        if message.get("tool_calls"):
            # LLM 要调用工具
            tool_call = message["tool_calls"][0]
            agent_name = tool_call["function"]["name"]  # ← 拿到的是agent名字
            agent_input = json.loads(tool_call["function"]["arguments"])["input"]
            print(f"[步骤{step+1}] 调用agent: {agent_name}， agent 输入：{agent_input}")
            
            # 3. 执行工具
            # 你来写这部分：根据 tool_name 调用对应的函数
            if agent_name == "rag_agent":
                result = rag_agent(agent_input)
            elif agent_name == "note_agent":
                result = note_agent(agent_input)
            else:
                result = "未知Agent"  # 加这行

            # 4. 把工具结果加入 history，让 LLM 观察
            history.append(message)
            history.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": str(result)
            })
        else:
            print(f"[步骤{step+1}] 返回最终答案")
            return message["content"]
    
    return "已达到最大步数，Agent 停止。"

if __name__ == "__main__":
    while True:
        user_input = input("你: ")
        if user_input.strip().upper() == "END":
            break
        result = orchestrator(user_input)
        print(f"Orchestrator: {result}\n")