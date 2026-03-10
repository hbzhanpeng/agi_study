"""
Week 5 Day 3 重修实战：底层 Function Calling 揭秘
目标：不依赖 LangChain，纯手工实现完整的 3 步 Function Calling 工作流。
这是面试最爱用的大招。
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import json
import requests
from dotenv import load_dotenv

# 加载 API Key
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'week4', '.env'))
API_KEY = os.getenv("SILICONFLOW_API_KEY")
BASE_URL = "https://api.siliconflow.cn/v1"

# ============================================================
# 1. 我们的本地真实函数 (本地代码库)
# ============================================================
def get_current_weather(location, unit="celsius"):
    """
    一个模拟的本地查天气函数
    """
    print(f"\n[🖥️ 本地系统日志] 正在调用真实天气 API 查询：{location}...")
    
    # 模拟网络请求返回数据
    if location in ["火星", "月球"]:
        raise ValueError(f"暂不支持外星天气查询API，当前仅支持地球城市。传入的城市为：{location}")
        
    weather_info = {
        "location": location,
        "temperature": "12" if unit == "celsius" else "55",
        "condition": "局部有微雨" if location == "北京" else "晴朗",
        "unit": unit
    }
    return json.dumps(weather_info, ensure_ascii=False)


# ============================================================
# TODO 1: 制作"函数说明书"（JSON Schema）发给大模型
# ============================================================
# 这是 Function Calling 最关键的一环，你不仅要写明有哪些参数，
# 甚至要告诉模型每个参数的类型（type）和必填项（required），
# 这样 LLM 才会变成完美的"JSON抽取机器"
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "获取指定位置的当前天气情况。如果是中国城市，直接填城市名。",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市或区县，例如：北京，海淀区"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"], # 限定类型
                        "description": "温度单位，中国必须使用 celsius"
                    }
                },
                "required": ["location"] # 指定哪些参数绝不能少
            }
        }
    }
]

# 统一请求封装
def call_deepseek(messages, tools=None):
    payload = {
        "model": "deepseek-ai/DeepSeek-V2.5",
        "messages": messages,
        "temperature": 0.1
    }
    # 只要带有工具列表，就放进 payload 里
    if tools:
        payload["tools"] = tools
        
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=30
    )
    return resp.json()["choices"][0]["message"]


# ============================================================
# TODO 2: 实现完整的三步走流程
# ============================================================
def run_weather_agent(user_query):
    # 初始化消息历史，我们作为用户第一次提问
    messages = [{"role": "user", "content": user_query}]
    print(f"👤 用户提问: {user_query}")
    print("-" * 40)

    # ----------------------------------------
    # 【第一步】带着工具说明书，去问 LLM
    # ----------------------------------------
    print("[1] 🤖 将问题 + 函数注册表同时发给 LLM...")
    first_responseMsg = call_deepseek(messages, tools=tools)
    
    # 关键点判断：LLM 是自己回答了，还是要调用工具？
    if first_responseMsg.get("tool_calls"):
        
        # 提取出所有的工具调用需求（可能一下子调用多个，我们只看第一个）
        tool_call = first_responseMsg["tool_calls"][0]
        func_name = tool_call["function"]["name"]
        
        # 参数全都被 LLM 完美变成了 JSON string
        func_args = json.loads(tool_call["function"]["arguments"])
        
        print(f"[2] 🧠 LLM 分析决定调用工具: `{func_name}`")
        print(f"    提取出的参数为: {func_args}")
        
        # 将 LLM 这个"我打算调用工具"的意图，原样存入历史消息！
        # 这个动作告诉历史上下文：这是 LLM 刚才的决定
        messages.append(first_responseMsg)
        
        # ----------------------------------------
        # 【第二步】本地代码实际执行查天气
        # ----------------------------------------
        # TODO: 这里需要你来补充！
        # 1. 提取出位置参数 location
        # 2. 调用 get_current_weather(location=..., unit=...) 
        # 3. 拿到 function_response
        
        # >>> 请在这里填写真正的调用代码 >>>
        location = func_args.get("location")
        unit = func_args.get("unit", "celsius") 
        
        try:
            function_response = get_current_weather(location, unit)
            print(f"[3] ✅ 本地执行成功，原始 JSON 结果: {function_response}")
        except Exception as e:
            # 🚨 核心防御思路：把报错用 JSON 包装起来扔回给大模型处理！
            print(f"[3] ❌ 本台执行报错，拦截异常并返回给 LLM: {str(e)}")
            function_response = json.dumps({"error": str(e)}, ensure_ascii=False)
        # <<< 填写结束 <<<
        
        # ----------------------------------------
        # 【第三步】把工具结果喂给模型，让它"翻译"成人话
        # ----------------------------------------
        # 这是 Function Calling 固定专用的 role:"tool"
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "name": func_name,
            "content": function_response
        })
        
        print("[4] 🗣️ 将结果再次发给 LLM，让其转换为人话总结...")
        second_responseMsg = call_deepseek(messages)
        return second_responseMsg["content"]
        
    else:
        # LLM 觉得没必要调工具，直接就回答了
        return first_responseMsg["content"]

if __name__ == "__main__":
    print("============================================================")
    print("🌦️ 深入底层：手写完整 Function Calling 流程分析")
    print("============================================================")
    
    # 测试问题 1
    final_answer = run_weather_agent("北京今天多少度？要不要带伞？")
    print(f"\n💡 最终流利的人话回答: {final_answer}\n")
    
    print("============================================================")
    
    # 测试问题 2: 让它产生多点推理
    final_answer2 = run_weather_agent("我媳妇去上海出差了，她那边天气适合穿薄衬衫吗？")
    print(f"\n💡 最终流利的人话回答: {final_answer2}\n")
    
    print("============================================================")
    
    # 🚨 测试问题 3: 体验终极兜底功能：给一个故意报错的城市
    final_answer3 = run_weather_agent("帮我看看火星的天气怎么样，我要穿宇航服吗？")
    print(f"\n💡 最终流利的人话回答: {final_answer3}\n")
