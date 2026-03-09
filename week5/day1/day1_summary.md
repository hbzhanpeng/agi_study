# 第 5 周 Day 1 学习总结：AI Agent 核心概念

> **核心目标：理解 Agent 四大组件和 ReAct 工作流。**

---

## 1. 什么是 AI Agent

**一句话**：Agent = LLM + 工具调用 + 自主规划

- 普通 LLM：被动回答
- AI Agent：主动规划 + 执行操作

---

## 2. Agent 四大组件（面试必背）

| 组件 | 作用 | 前端类比 |
|------|------|---------|
| **LLM** | 思考推理 | JavaScript 引擎 |
| **Tools** | 执行操作 | fetch / axios |
| **Memory** | 记忆存储 | localStorage + Redux |
| **Planning** | 任务规划 | React Router |

---

## 3. ReAct 工作流

```
Thought → 想清楚下一步做什么
Action  → 调用一个具体工具
Observation → 观察工具返回结果
（循环直到任务完成）
Answer → 返回最终结果
```

**关键**：一个 Action 只做一件事，对应一个工具调用

---

## 4. Agent 规划策略

| 策略 | 特点 | 适用场景 |
|------|------|---------|
| **ReAct** | 走一步想一步 | 简单交互 |
| **Plan-and-Execute** | 先列完整计划再执行 | 多步骤复杂任务 |
| **Reflexion** | 做完后自我反思改进 | 高质量输出（代码/写作）|

---

## 5. Agent vs RAG

| 维度 | RAG | Agent |
|------|-----|-------|
| 能力 | 只能"读" | 能"读+写+做" |
| 工具 | 只用向量检索 | 可调用任意工具 |
| 自主性 | 被动回答 | 主动规划+执行 |

---

## 5. 下一步学习

**Day 2 内容**：Function Calling 实战（Agent 的核心能力）
