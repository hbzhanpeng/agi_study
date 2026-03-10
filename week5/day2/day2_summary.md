# 第 5 周 Day 2 学习总结：LangChain 深度

> **核心目标：理解 LangChain 5 大组件的内部原理，手写 Mini-LangChain。**

---

## 1. LangChain 五大组件

| 组件 | 作用 | 前端类比 |
|------|------|---------|
| **Chain** | 串联多步骤 | Promise.then().then() |
| **Agent** | LLM 自主决策 | 全栈应用 |
| **Tool** | 工具注册 | Express 路由 |
| **Memory** | 对话记忆 | Redux + localStorage |
| **Callback** | 生命周期钩子 | React useEffect |

---

## 2. Memory 三种类型（面试必背）

| 类型 | 原理 | 适用场景 |
|------|------|---------|
| **Buffer** | 保存全部对话 | 对话轮次少（<10轮）|
| **Summary** | LLM 压缩为摘要 | 对话轮次多 |
| **VectorStore** | 向量化存储 | 长期记忆，按相关性检索 |

---

## 3. LCEL 表达式

```python
# 用 | 管道符串联组件（类似 Unix 管道）
chain = prompt | llm | output_parser
result = chain.invoke("问题")
```

优势：简洁、原生支持 streaming/async/batch

---

## 4. LangChain vs LlamaIndex

| 框架 | 定位 | 适用场景 |
|------|------|---------|
| **LangChain** | 通用 LLM 应用框架 | Agent、工具编排 |
| **LlamaIndex** | 数据+检索框架 | RAG、知识库 |

---

## 5. 实战：手写 Mini-LangChain

`mini_langchain.py` 从零实现了 5 大组件：

### 核心代码
```python
# Tool 注册
class Tool:
    def __init__(self, name, description, func):
        self.name = name          # LLM 靠 name 识别
        self.description = description  # LLM 靠 description 选工具！
        self.func = func

# Buffer Memory
class ConversationBufferMemory:
    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
    def get_history(self):
        return "\n".join([...])

# Summary Memory（每 3 条 LLM 压缩）
class ConversationSummaryMemory:
    def add_message(self, role, content):
        if self.message_count % 3 == 0:
            self.summary = self.llm.call(f"总结：{self.summary}")
```

### 踩坑记录
- `__init_` 少一个下划线 → 构造函数不生效
- Tool 的 description 非常重要 → LLM 靠它选工具

---

## 6. 深度实战：带记忆的对话 Agent

`chat_agent.py` 实现了 Memory + Tool 组合的多轮对话 Agent。

### 核心设计：双层记忆

```python
长期记忆（Memory）     = 只存 user + assistant（跨轮持久化）
短期记忆（Working Memory）= 当前任务的工具结果（用完即弃）
```

### 踩坑（面试高频考点）
- ❌ 把工具结果存到长期记忆 → 记忆污染 → Agent 记不住用户名
- ❌ 循环没有兜底 return → 返回 None
- ✅ 工具结果只存 working_memory，任务完成后丢弃

### LangChain 生态补充
- **LangSmith**：调试+监控（类似 Sentry）
- **LangServe**：部署（Chain → REST API）
- **LangGraph**：复杂流程编排（状态机）
- **LlamaIndex**：专注 RAG，和 LangChain 互补

---

## 7. 下一步学习

**Day 3 内容**：工具调用（Function Calling 原理、工具注册/描述/校验、错误处理）
