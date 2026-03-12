# 第 5 周 Day 7 学习总结：自主 Agent 综合实战

> **核心目标：整合 Week 5 所有知识点（ReAct + Function Calling + Memory + Reliability），构建能上网搜索、读写文件、生成代码的生产级自主 Agent，并掌握其架构设计的面试深度回答点。**

---

## 1. 为什么要学这个？

前 6 天学了 Agent 的各个组件，但都是"单点技能"。真实场景中，Agent 需要：

```
用户："帮我查一下 Python 3.12 的新特性，总结成 Markdown 保存到 features.md"

需要的能力：
1. 搜索网络（获取实时信息）
2. 理解搜索结果（LLM 推理）
3. 生成 Markdown（内容创作）
4. 写入文件（文件操作）
```

**这就是自主 Agent**：能自己规划步骤、调用工具、完成复杂任务。

**面试为什么爱考**：
- 考察你对 Agent 全链路的理解（不是只会调 API）
- 考察工程能力（错误处理、工具设计、可靠性）
- 考察架构思维（如何拆解复杂任务）

---

## 2. 自主 Agent 核心架构

### 2.1 四大核心组件

| 组件 | 作用 | 对应代码 |
|------|------|---------|
| **工具库 (Tools)** | 定义 Agent 能做什么 | `_define_tools()` |
| **推理引擎 (LLM)** | 决策下一步做什么 | `_call_llm()` |
| **执行器 (Executor)** | 调用具体工具 | `_execute_tool()` |
| **控制循环 (Loop)** | ReAct 循环直到完成 | `run()` |

### 2.2 ReAct 循环流程

```
用户输入 → LLM 推理 → 决定调用工具 → 执行工具 → 观察结果 → LLM 再推理 → ...
         ↑_______________________________________________|
                        (循环直到任务完成)
```

### 面试考点

**问**："自主 Agent 和普通对话的区别是什么？"

**答**：
> "普通对话是一问一答，Agent 是多步规划。Agent 有工具调用能力，能主动获取信息、执行操作。核心是 ReAct 循环：Reasoning（推理下一步）→ Action（调用工具）→ Observation（观察结果）→ 再推理，直到任务完成。"

---

## 3. 工具定义与注册

### 3.1 工具定义格式

```python
{
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "搜索网络获取实时信息",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"}
            },
            "required": ["query"]
        }
    }
}
```

**关键点**：
- `name`：工具名称（LLM 会根据这个决定调用哪个工具）
- `description`：工具功能描述（越清晰，LLM 越准确）
- `parameters`：参数 schema（JSON Schema 格式）

### 3.2 四大工具实现

```python
def search_web(self, query: str) -> str:
    try:
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json"},
            timeout=5
        )
        data = response.json()
        return data.get("AbstractText", f"搜索结果: {query}")
    except Exception as e:
        return f"搜索失败: {str(e)}"

def read_file(self, file_path: str) -> str:
    try:
        if not os.path.exists(file_path):
            return f"文件不存在: {file_path}"
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"读取失败: {str(e)}"

def write_file(self, file_path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"成功写入: {file_path}"
    except Exception as e:
        return f"写入失败: {str(e)}"

def generate_code(self, description: str, language: str, file_path: str) -> str:
    try:
        prompt = f"生成{language}代码: {description}\n只返回代码，不要解释。"
        messages = [{"role": "user", "content": prompt}]
        response = self._call_llm(messages)
        code = response["choices"][0]["message"]["content"]
        self.write_file(file_path, code)
        return f"代码已生成并保存到: {file_path}"
    except Exception as e:
        return f"生成失败: {str(e)}"
```

### 面试考点

**问**："工具定义的 description 为什么重要？"

**答**：
> "description 是 LLM 选择工具的唯一依据。如果写得模糊，LLM 可能选错工具或传错参数。好的 description 要说清楚：什么场景用、输入是什么、输出是什么。比如 'search_web' 要写'搜索网络获取实时信息'，而不是只写'搜索'。"

---
## 4. ReAct 循环实现

### 4.1 核心循环逻辑

```python
def run(self, user_input: str, max_iterations: int = 5) -> str:
    self.conversation_history.append({"role": "user", "content": user_input})
    
    for i in range(max_iterations):
        response = self._call_llm(self.conversation_history)
        message = response["choices"][0]["message"]
        
        if message.get("tool_calls"):
            self.conversation_history.append(message)
            
            for tool_call in message["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])
                result = self._execute_tool(tool_name, arguments)
                
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result
                })
        else:
            return message["content"]
    
    return "达到最大迭代次数"
```

### 4.2 关键设计点

| 设计点 | 原因 |
|--------|------|
| `max_iterations=5` | 防止死循环，Day 6 学的循环检测 |
| `conversation_history` | 保存上下文，让 LLM 知道之前做了什么 |
| `tool_call_id` | OpenAI API 要求，用于关联工具调用和结果 |
| `json.loads(arguments)` | 工具参数是 JSON 字符串，需要解析 |

### 面试考点

**问**："为什么要设置 max_iterations？"

**答**：
> "防止 Agent 陷入死循环。比如工具一直失败，Agent 可能一直重试。设置上限后，达到最大次数就强制终止，返回错误信息。这是 Day 6 学的循环检测机制的一种实现。"

**问**："conversation_history 为什么要保存工具调用结果？"

**答**：
> "因为 LLM 是无状态的，每次调用都需要完整上下文。如果不保存工具结果，LLM 不知道上一步做了什么，可能重复调用相同工具。保存后，LLM 能根据结果决定下一步，形成完整的推理链。"

---

## 5. 工具执行与错误处理

### 5.1 工具分发器

```python
def _execute_tool(self, tool_name: str, arguments: Dict) -> str:
    if tool_name == "search_web":
        return self.search_web(arguments["query"])
    elif tool_name == "read_file":
        return self.read_file(arguments["file_path"])
    elif tool_name == "write_file":
        return self.write_file(arguments["file_path"], arguments["content"])
    elif tool_name == "generate_code":
        return self.generate_code(
            arguments["description"],
            arguments["language"],
            arguments["file_path"]
        )
    return "Unknown tool"
```

### 5.2 错误处理策略

| 错误类型 | 处理方式 | 原因 |
|---------|---------|------|
| 工具不存在 | 返回 "Unknown tool" | 让 LLM 知道工具不可用，重新规划 |
| 参数缺失 | 返回错误信息 | 让 LLM 修正参数后重试 |
| 执行失败 | 返回异常信息 | 让 LLM 根据错误决定下一步 |
| 网络超时 | 返回超时信息 | 可以触发重试或换工具 |

### 面试考点

**问**："工具执行失败怎么处理？"

**答**：
> "不要直接抛异常，而是返回错误信息给 LLM。因为 LLM 能理解错误并调整策略。比如文件不存在，LLM 可能先创建目录；网络超时，LLM 可能换个工具或重试。这是 Day 6 学的失败恢复机制的应用。"

---

## 6. 可靠性机制集成

### 6.1 Day 6 四大机制的应用

```python
class ReliableAgent(AutonomousAgent):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.action_history = []
        self.max_same_action = 3
    
    def _execute_tool_with_validation(self, tool_name: str, args: Dict) -> str:
        if tool_name not in ["search_web", "read_file", "write_file", "generate_code"]:
            return "工具不存在"
        
        action = f"{tool_name}({args})"
        self.action_history.append(action)
        
        recent = self.action_history[-self.max_same_action:]
        if len(set(recent)) == 1 and len(recent) == self.max_same_action:
            return "检测到重复操作，已终止"
        
        if tool_name == "write_file" and self._is_high_risk(args):
            return "需要人工确认"
        
        return self._execute_tool(tool_name, args)
    
    def _is_high_risk(self, args: Dict) -> bool:
        dangerous_paths = ["/etc/", "/sys/", "C:\Windows\\"]
        file_path = args.get("file_path", "")
        return any(path in file_path for path in dangerous_paths)
```

### 6.2 四大机制对比

| 机制 | 在自主 Agent 中的应用 |
|------|---------------------|
| 幻觉检测 | 检查工具名是否存在、参数是否完整 |
| 失败恢复 | 返回错误信息让 LLM 重试或换工具 |
| 循环检测 | `max_iterations` + 重复动作检测 |
| Human-in-the-Loop | 高风险文件操作需要人工确认 |

### 面试考点

**问**："自主 Agent 如何防止误删重要文件？"

**答**：
> "两层防护：第一层是路径白名单，禁止操作系统目录；第二层是 Human-in-the-Loop，删除操作需要人工确认。实现上，在 _execute_tool 前检查路径，如果是高风险路径，返回'需要人工确认'，暂停执行等待用户批准。"

---

## 7. 实战代码

文件路径：`week5/day7/autonomous_agent.py`

**核心实现**：

```python
class AutonomousAgent:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.conversation_history = []
        self.tools = self._define_tools()
    
    def run(self, user_input: str, max_iterations: int = 5) -> str:
        self.conversation_history.append({"role": "user", "content": user_input})
        
        for i in range(max_iterations):
            response = self._call_llm(self.conversation_history)
            message = response["choices"][0]["message"]
            
            if message.get("tool_calls"):
                self.conversation_history.append(message)
                for tool_call in message["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    arguments = json.loads(tool_call["function"]["arguments"])
                    result = self._execute_tool(tool_name, arguments)
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result
                    })
            else:
                return message["content"]
        
        return "达到最大迭代次数"
```

**测试用例**：

```python
agent = AutonomousAgent(api_key="your-key")

result = agent.run("查一下 Python 3.12 的新特性，总结成 Markdown 保存到 features.md")

```

**预期输出**：
```
步骤 1: 调用 search_web("Python 3.12 new features")
步骤 2: LLM 总结搜索结果
步骤 3: 调用 write_file("features.md", "# Python 3.12 新特性\n...")
步骤 4: 返回 "已保存到 features.md"
```

---
## 8. 真实踩坑经历

**事故 1：工具参数 JSON 解析失败**
> LLM 有时会在 JSON 参数里加 Markdown 代码块标记，比如 ` ```json\n{"query": "..."}\n``` `，导致 `json.loads` 直接报错，整个 Agent 崩溃。
**经验**：
> 永远不要裸调 `json.loads`。用正则先提取 `{...}` 块，或者用 try/except 捕获后让 LLM 重新生成参数。

**事故 2：文件路径跨平台问题**
> 在 Windows 上开发的 Agent，LLM 生成的路径用了 `/` 分隔符，在 Windows 上 `os.path.exists` 有时能识别，有时不能，导致"文件不存在"的假报错。
**经验**：
> 统一用 `pathlib.Path` 处理路径，它会自动处理跨平台差异。`Path(file_path).exists()` 比 `os.path.exists(file_path)` 更可靠。

**事故 3：generate_code 生成的代码包含 Markdown 代码块**
> LLM 生成代码时，经常会加上 ` ```python\n...\n``` ` 包裹，直接保存到 .py 文件后无法运行。
**经验**：
> 保存前用正则清理：`re.sub(r'```\w*\n?', '', code).strip()`。或者在 prompt 里明确说"只返回纯代码，不要 Markdown 格式"。

---

**导师寄语**：
> 今天你完成了 Week 5 的收官之作。自主 Agent 是 AGI 应用开发的核心能力，面试官最爱问的就是"你设计过什么 Agent？遇到过什么问题？怎么解决的？"。记住：Agent 够不够聪明看 LLM，但 Agent 够不够可靠、能不能上线，看的是你今天写的这些工程细节。

**下一步**：第六周 — 模型微调与训练基础（LoRA/QLoRA、RLHF/DPO）⭐⭐⭐⭐⭐
