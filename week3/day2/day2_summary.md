# 第 3 周 Day 2 学习总结：Prompt Engineering 系统化

> **核心目标：掌握 CoT/ToT/ReAct 等推理框架的原理和使用场景。**

---

## 1. Chain of Thought（CoT）—— 思维链

### 核心思想
让模型"一步步思考"，不跳步，展示完整推理过程。

### 三种变体

| 变体 | 做法 | 适用场景 |
|------|------|---------|
| Zero-Shot CoT | 加一句 "Let's think step by step" | 快速提升推理准确率 |
| Few-Shot CoT | 给带推理步骤的示例 | 复杂任务 |
| Self-Consistency | 多次采样取多数票 | 提高可靠性 |

### Zero-Shot CoT 魔法咒语
```
[问题]
Let's think step by step.
```

仅此一句话，数学推理准确率可提升 10-20%！

### 产品级 Prompt 设计
```
System Prompt:
你是一位耐心的数学老师。回答问题时请：
1. 确认题意
2. 列出已知条件
3. 写出解题步骤（Step 1, Step 2...）
4. 给出最终答案并用 ✅ 标注
Let's think step by step.
```

---

## 2. Tree of Thought（ToT）—— 思维树

### 核心思想
多条路径探索 + 评估 + 选最优

```
CoT：一条线思考  → Step1 → Step2 → 答案
ToT：多条路径    → 方案A / 方案B / 方案C → 选最优
```

### Prompt 模板
```
想象三位专家在解决这个问题。
每位独立给出思路，然后互相讨论选最优方案。
```

### 适用场景
- 创意类（取名、文案）
- 开放性问题（方案设计）
- 需要对比多种方案的决策

---

## 3. ReAct —— 思考 + 行动 + 观察

### 核心思想
让模型不仅思考，还能调用外部工具获取信息

```
Thought → Action → Observation → Thought → Answer
（想）    （做）    （看结果）    （继续想）  （给答案）
```

### 适用场景
- 需要实时数据（天气、股价）
- 需要外部工具（搜索、数据库、API）
- Agent 的核心范式

---

## 4. 框架选择决策树（面试必背）

```
任务类型判断：
├── 有明确解题步骤？ → CoT
├── 需要外部数据/工具？ → ReAct
├── 需要创造力/多方案？ → ToT
└── 需要高可靠性？ → Self-Consistency
```

---

## 5. 避坑指南

1. **不是所有任务都需要 CoT** → 简单问答加了反而更慢更贵
2. **CoT 增加 token 成本** → 线上要权衡准确率 vs 成本
3. **英文触发词效果更好** → "Let's think step by step" > "让我们一步步思考"
4. **产品中 CoT 应内置** → 放在 System Prompt 里，不依赖用户输入

---

## 6. 下一步学习

**明天内容**：System Prompt 设计模式 + Function Calling

**预习问题**：
1. System Prompt 和 User Prompt 有什么区别？
2. Function Calling 是怎么让模型"调工具"的？
