# 第 4 周 Day 4 学习总结：检索策略 + RAG 实战

> **核心目标：掌握三种检索方式 + 跑通完整 RAG 链路。**

---

## 1. 三种检索方式（面试必背）

| 方式 | 原理 | 擅长 | 不擅长 |
|------|------|------|--------|
| **Dense** | Embedding 语义匹配 | 语义理解（换说法也能找到）| 精确关键词 |
| **Sparse** | BM25 关键词匹配 | 精确匹配专有名词 | 语义理解 |
| **Hybrid ✅** | 两者结合 | 最全面 | 略复杂 |

### Rerank（重排序）
- 检索 Top 20 → 用精排模型重新排序 → 返回 Top 5
- 类比：海选 20 人 → 复试精选 5 人

---

## 2. RAG 实战代码（完整链路跑通！）

### 架构
```
文档(5篇) → BGE Embedding → 1024维向量
用户提问 → BGE Embedding → 余弦相似度检索 → Top 2 文档
[文档+问题] → DeepSeek → 生成回答
```

### 核心代码
```python
# 余弦相似度
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# 检索
scores = [cosine_similarity(chunk_emb, query_emb) for chunk_emb in chunk_embeddings]
top_indices = np.argsort(scores)[::-1][:top_k]

# RAG Prompt
prompt = f"""
你是企业知识库助手，根据参考资料回答问题。
参考资料：{context}
用户问题：{question}
"""
```

### 踩坑记录
- `.env` 路径要注意相对位置（脚本在 day4/，.env 在 week4/）
- Prompt 要用 **f-string**，否则 `{context}` 不会被替换

---

## 3. 面试考点

- **Dense vs Sparse vs Hybrid**：向量语义匹配 vs 关键词匹配 vs 两者结合
- **为什么用 Hybrid**：取长补短，向量找语义，关键词找精确
- **Rerank**：二次精排提升准确率

---

## 4. 下一步学习

**Day 5 内容**：RAG 进阶（Query 改写、HyDE、Self-RAG）
