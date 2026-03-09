# 第 4 周 Day 6 学习总结：RAG 评估体系

> **核心目标：掌握 RAG 评估三大指标 + 自动化评估实战。**

---

## 1. RAG 评估三角（面试必背）

| 指标 | 评估什么 | 差的表现 | 好的表现 |
|------|---------|---------|---------|
| **Context Relevance** | 检索到的文档相关吗 | 问年假，检索到加班 | 问年假，检索到年假 |
| **Faithfulness** | 回答基于文档吗 | 文档说15天，答20天 | 文档说15天，答15天 |
| **Answer Relevance** | 回答了问题吗 | 问几天年假，答申请流程 | 问几天年假，答15天 |

---

## 2. RAGAS 框架

- 用 **LLM 当评委**，自动评估不需人工标注
- 指标和手写的一一对应，但语义理解更智能
- `pip install ragas` 即可使用

---

## 3. 实战：自动化评估脚本

### 核心代码
```python
# Context Relevance: 关键词命中检测
def eval_context_relevance(test_item, search_results):
    for result in search_results:
        if test_item["expected_doc_keyword"] in result["chunk"]:
            return 1
    return 0

# Answer Relevance: 期望答案包含检测
def eval_answer_relevance(test_item, answer):
    if test_item["expected_answer"] in answer:
        return 1
    return 0
```

### 运行结果
```
Context Relevance（检索准确率）: 4/4 = 100%
Answer Relevance（回答准确率）: 4/4 = 100%
🎉 效果优秀！
```

### 踩坑记录
- `answer` 是字符串不是列表，不能用 `for` 遍历后取 `["answer"]`
- API 多次调用导致评估慢 → 实际项目用 Embedding 缓存 + 批量请求

---

## 4. 性能优化经验

- 文档 Embedding 只算一次存到向量库（不每次重算）
- 批量请求合并多个问题
- 异步并发发请求不排队

---

## 5. 下一步学习

**Day 7 内容**：第 4 周综合复习 + RAG 综合实战
