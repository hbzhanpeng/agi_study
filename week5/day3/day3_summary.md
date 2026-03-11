# 第 5 周 Day 3 学习总结：Function Calling 原理与工程实践

> **核心目标：深入理解 Function Calling 的完整生命周期，掌握错误处理和兜底机制，能在面试中画出完整流程图。**

---

## 1. 为什么需要 Function Calling？

### 纯 Prompt 的致命缺陷

```python
# ❌ 纯 Prompt 方式（不稳定）
prompt = """
你必须只返回合法 JSON，格式如下：
{"city": "城市名", "date": "日期"}

用户问题：明天北京天气怎么样？
"""

# 可能的输出：
"好的，这是你要的内容：{\"city\": \"北京\", \"date\": \"明天\"}"  # 多余文字
"{city: '北京', date: '明天'}"  # 单引号，不是合法 JSON
"{'city': '火星', 'date': '明天'}"  # 幻觉参数
```

**三大问题**：
1. **格式不稳定**：容易出现多余文字，导致 `JSON.parse()` 崩溃
2. **参数幻觉**：私自捏造不存在的参数（如"火星"）
3. **浪费 Token**：需要大量文字描述格式，且难以应对复杂参数结构

### Function Calling 的优势

```
Function Calling = 大模型的硬约束提取协议
- 格式 100% 稳定（OpenAI 保证返回合法 JSON）
- 参数有 schema 约束（类型、必填、枚举值）
- 节省 Token（不需要描述格式）
- 支持复杂嵌套结构
```

---

## 2. Function Calling 完整流程（面试必背）

### Two-Turn 工作流

```
┌─────────────────────────────────────────────────────┐
│                    第 1 轮：决策                      │
│                                                     │
│  用户 → LLM                                          │
│  ├─ messages: [{"role": "user", "content": "..."}]  │
│  └─ tools: [函数 schema 定义]                        │
│                                                     │
│  LLM → 开发者                                        │
│  └─ tool_calls: [                                   │
│       {                                             │
│         "id": "call_abc123",                        │
│         "type": "function",                         │
│         "function": {                               │
│           "name": "get_weather",                    │
│           "arguments": "{\"city\": \"北京\"}"        │
│         }                                           │
│       }                                             │
│     ]                                               │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                    第 2 步：执行                      │
│                                                     │
│  开发者本地代码                                       │
│  ├─ 解析 tool_calls                                 │
│  ├─ 调用本地函数 get_weather(city="北京")            │
│  └─ 得到结果：{"temp": 25, "weather": "晴"}          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                    第 2 轮：生成                      │
│                                                     │
│  开发者 → LLM                                        │
│  └─ messages: [                                     │
│       原始对话,                                      │
│       LLM 的 tool_calls,                            │
│       {                                             │
│         "role": "tool",                             │
│         "tool_call_id": "call_abc123",              │
│         "content": "{\"temp\": 25, \"weather\": \"晴\"}" │
│       }                                             │
│     ]                                               │
│                                                     │
│  LLM → 用户                                          │
│  └─ "北京今天晴，气温 25 度。"                         │
└─────────────────────────────────────────────────────┘
```

**⚠️ 面试最容易答错的问题**：
> "谁执行了函数？"
> 
> 答：**开发者的本地代码**，不是 LLM，不是 OpenAI 服务器。
> 
> LLM 只负责"决策"（调什么函数、传什么参数），执行永远是你的代码。

---

## 3. 函数 Schema 定义

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如：北京、上海"
                    },
                    "date": {
                        "type": "string",
                        "enum": ["今天", "明天", "后天"],
                        "description": "日期"
                    }
                },
                "required": ["city"],
                "additionalProperties": False
            }
        }
    }
]
```

**Schema 设计原则**：
- `description` 要详细，LLM 靠这个理解函数用途
- 用 `enum` 约束枚举值，防止幻觉
- 用 `required` 标记必填字段
- 复杂参数用嵌套 `object`

---

## 4. 完整代码实现

```python
import json
from openai import OpenAI

client = OpenAI(api_key="your-key")

def get_weather(city: str, date: str = "今天") -> dict:
    return {"city": city, "date": date, "temp": 25, "weather": "晴"}

def run_conversation(user_query: str):
    messages = [{"role": "user", "content": user_query}]
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    message = response.choices[0].message
    
    if not message.tool_calls:
        return message.content
    
    messages.append(message)
    
    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        if function_name == "get_weather":
            result = get_weather(**function_args)
        else:
            result = {"error": f"未知函数: {function_name}"}
        
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False)
        })
    
    final_response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    
    return final_response.choices[0].message.content
```

---

## 5. 错误处理与兜底机制（生产必备）

### 问题：参数错误导致函数执行失败

```python
def execute_function_with_error_handling(function_name, function_args):
    try:
        if function_name == "get_weather":
            result = get_weather(**function_args)
            return {"success": True, "data": result}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "函数执行失败，请检查参数"
        }

messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": json.dumps(result, ensure_ascii=False)
})
```

**为什么这样设计**：
- LLM 看到错误信息后，会自动给出友好的回复
- 可能尝试调用其他工具补救
- 避免直接把技术错误暴露给用户

---

## 6. 面试考点汇总

### 问法 1："Function Calling 的完整流程是什么？"

**标准答案**：
> "分两轮：第 1 轮，用户问题 + tools schema 发给 LLM，LLM 返回 tool_calls（函数名 + 参数 JSON）；第 2 步，开发者代码在本地执行函数，得到结果；第 2 轮，把执行结果以 role='tool' 加入对话历史，再发给 LLM，LLM 基于结果生成最终回答。"

### 问法 2："谁执行了函数？"

**标准答案**：
> "开发者的本地代码执行，不是 LLM，不是 OpenAI 服务器。LLM 只负责决策（调什么函数、传什么参数），执行永远是你的代码。类比：LLM 是大脑（指挥），开发者代码是手脚（执行）。"

### 问法 3："如果函数执行失败怎么办？"

**标准答案**：
> "用 try-catch 包裹函数调用，把错误信息包装成 JSON（不要直接抛异常），以 role='tool' 回传给 LLM。LLM 看到错误后会自动给出友好回复，或者尝试调用其他工具补救。这是生产环境的标准做法。"

---

## 7. 真实踩坑经历

**坑 1：忘记把 tool_calls 加入对话历史**
> 第 2 轮调用时，只把 tool 结果加入 messages，忘记加 LLM 的 tool_calls，导致 LLM 不知道自己调用了什么函数，回答乱七八糟。正确做法：`messages.append(message)` 保存 LLM 的完整响应。

**坑 2：函数执行失败直接抛异常**
> 早期直接 `raise Exception`，导致用户看到 500 错误。改成把错误信息包装成 JSON 回传给 LLM 后，LLM 会自动圆场："抱歉，查询失败，请稍后重试"。

**坑 3：schema description 写得太简单**
> 一开始 description 只写"获取天气"，LLM 经常搞不清楚什么时候该调用。改成"获取指定城市的实时天气信息，包括温度、天气状况"后，LLM 决策准确率大幅提升。

---

**导师寄语**：
> Function Calling 是 Agent 的核心能力，面试官问这个是想看你有没有真正做过工具调用。记住：LLM 只是大脑（决策），执行永远是你的代码。错误处理要用 try-catch + JSON 包装，不要直接抛异常。这两点能说清楚，这道题就过了。

**下一步**：Week5 Day4 — 记忆系统
