# 第 3 周 Day 7 学习总结：第 3 周综合复习

> **核心目标：巩固 LLM API 与 Prompt Engineering 全部知识。**

---

## 第 3 周知识图谱

```
Day1: API 参数 → temperature/top_p/max_tokens/stop/penalty
Day2: 推理框架 → CoT / ToT / ReAct / Self-Consistency
Day3: System Prompt 六大设计模式 + Function Calling
Day4: Prompt 注入攻防（输入清洗→Classifier→System Prompt加固→输出校验）
Day5: 多模态 API + 模型选型四维评估 + 分级路由
Day6: 国产模型对比 + 适配层设计（适配器模式）
Day7: 综合复习
```

---

## 综合复习成绩

| 题号 | 主题 | 结果 |
|------|------|------|
| Q1 | CoT 适用场景 | ✅ |
| Q2 | System Prompt 设计模式 | ✅ |
| Q3 | Function Calling 执行方 | ❌ → 正确答案：开发者的代码 |
| Q4 | Prompt 注入第一道防线 | ✅ |
| Q5 | 国产模型优势 | ✅ |

### ❗ 错题重点

**Function Calling 执行方**：
- 模型只做"决策"（调什么函数、传什么参数）
- **执行**是开发者的代码做的，不是 OpenAI 服务器
- 类比：模型 = 大脑（指挥），开发者代码 = 手脚（执行）

---

## 第 3 周完结！🎉

### 下一步：第 4 周 — RAG 系统

这是**面试重灾区**，几乎 100% 会问！内容包括：
- RAG 核心架构（Indexing → Retrieval → Generation）
- 文档处理流水线（PDF 解析、文本分块）
- Embedding 模型选型 + 向量数据库
- 检索策略（Dense/Sparse/Hybrid）
- RAG 评估体系
