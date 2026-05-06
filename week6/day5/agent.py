import os
import requests
import json
from rag import ask, add_note, call_llm_stream
from config import API_KEY, LLM_BASE_URL, CHAT_MODEL


tools = [
    {
        "type": "function",
        "function": {
            "name": "add_note",
            "description": "把一条笔记存入知识库",
            "parameters": {
                "type": "object",
                "properties": {
                    "note": {
                        "type": "string",
                        "description": "要存入的笔记内容"
                    }
                },
                "required": ["note"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_rag",
            "description": "查询用户的个人知识库，获取用户自己记录的踩坑经验和解决方案。当用户询问技术问题时，必须先调用此工具查询个人知识库，再回答。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "要问的问题"
                    }
                },
                "required": ["question"]
            }
        }
    }
]

def call_llm_with_tools(tools: list, history: list = None) -> dict:
    if history is None:
        history = []
        
    messages = list(history)
        
    resp = requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": CHAT_MODEL,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 500,
            "tools": tools
        },
        timeout=120
    )
    return resp.json()["choices"][0]["message"]


def run_agent(user_input: str) -> str:
    """Agent 主循环：思考 → 调用工具 → 观察 → 继续"""
    history = [
        {"role": "system", "content": "你是一个知识库助手。用户询问技术问题时，必须先调用ask_rag工具查询个人知识库，基于知识库内容回答。用户要存笔记时，调用add_note工具。"},
        {"role": "user", "content": user_input}
    ]
    max_steps = 5  # 最多5步，防止死循环
    for step in range(max_steps):

        message = call_llm_with_tools(tools, history)
        
        if message.get("tool_calls"):
            # LLM 要调用工具
            tool_call = message["tool_calls"][0]
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])
            print(f"[步骤{step+1}] 调用工具: {tool_name}，参数: {tool_args}")
            
            # 3. 执行工具
            # 你来写这部分：根据 tool_name 调用对应的函数
            if tool_name == "add_note":
                result = add_note(tool_args["note"])
            elif tool_name == "ask_rag":
                answer, sources = ask(tool_args["question"])
                result = f"{answer}\n{sources}"
            else:
                result = "未知工具"
            
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


def run_agent_stream(user_input: str):
    """流式版 Agent：工具调用阶段正常等待，最终回答阶段逐 token yield"""
    history = [
        {"role": "system", "content": (
            "你是用户的个人踩坑知识库助手。"
            "无论用户问什么，你都必须先调用 ask_rag 工具查询个人知识库，不能直接回答。"
            "如果知识库返回的内容相关，基于知识库内容回答。"
            "如果知识库没有相关内容，直接告诉用户'你的知识库里还没有这条记录'。"
            "用户要存笔记时，调用 add_note 工具。"
        )},
        {"role": "user", "content": user_input}
    ]
    max_steps = 5
    for step in range(max_steps):
        message = call_llm_with_tools(tools, history)

        # 第 0 步兜底：LLM 未调工具则强制查询
        if step == 0 and not message.get("tool_calls"):
            print(f"[步骤1] LLM 未调用工具，强制查询知识库")
            rag_answer, rag_sources = ask(user_input)
            history.append(message)
            history.append({
                "role": "user",
                "content": f"[知识库查询结果]\n{rag_answer}\n{rag_sources}\n\n请基于以上知识库内容回答用户的问题，如果知识库无相关内容请直接说明。"
            })
            continue

        if message.get("tool_calls"):
            tool_call = message["tool_calls"][0]
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])
            print(f"[步骤{step+1}] 调用工具: {tool_name}，参数: {tool_args}")

            if tool_name == "add_note":
                result = add_note(tool_args["note"])
            elif tool_name == "ask_rag":
                answer, sources = ask(tool_args["question"])
                result = f"{answer}\n{sources}"
            else:
                result = "未知工具"

            history.append(message)
            history.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": str(result)
            })
        else:
            # 最终回答阶段：使用真正的流式调用 (SSE)
            print(f"[步骤{step+1}] 流式返回最终答案")
            
            # 因为部分大模型遇到带 tool_calls 的 history 会拒绝流式输出，我们需要把历史“洗干净”
            clean_messages = []
            
            # 1. 提取出最后一次 RAG 返回的参考资料
            last_rag_result = ""
            for msg in history:
                if msg.get("role") == "tool" and "相似度" in msg.get("content", ""):
                    last_rag_result = msg.get("content")
            
            # 2. 仅保留 user 和 system 信息（或者无 tool_calls 的 assistant 历史对话）
            for msg in history:
                if msg.get("role") in ["system", "user"]:
                    clean_messages.append(msg)
                elif msg.get("role") == "assistant" and not msg.get("tool_calls"):
                    clean_messages.append(msg)
                    
            # 3. 把提取出来的资料强制塞给最后的提问，变成一个纯纯的“基于背景回答问题”的新请求
            if last_rag_result and len(clean_messages) > 0 and clean_messages[-1]["role"] == "user":
                original_question = clean_messages[-1]["content"]
                clean_messages[-1]["content"] = f"知识库查询结果如下：\n{last_rag_result}\n\n请基于以上内容回答我的问题：{original_question}"

            for chunk in call_llm_stream(clean_messages):
                yield chunk
            return

    yield "已达到最大步数，Agent 停止。"


if __name__ == "__main__":
    while True:
        user_input = input("你: ")
        if user_input.strip().upper() == "END":
            break
        result = run_agent(user_input)
        print(f"Agent: {result}\n")