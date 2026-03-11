# 第 4 周 Day 4 学习总结：检索策略 + RAG 实战

> **核心目标：掌握三种检索方式的原理和适用场景，能在面试中说清楚为什么用混合检索，跑通完整 RAG 链路。**

---

## 1. 三种检索方式（面试必背）

| 方式 | 原理 | 擅长 | 不擅长 | 适用场景 |
|------|------|------|--------|---------|
| **Dense（向量检索）** | Embedding 语义匹配 | 语义理解（换说法也能找到） | 精确关键词 | 通用问答 |
| **Sparse（关键词检索）** | BM25 词频匹配 | 精确匹配专有名词 | 语义理解 | 专有名词查询 |
| **Hybrid（混合检索）✅** | 两者结合 | 最全面 | 略复杂 | **生产环境首选** |

### 1.1 Dense 检索（向量检索）

```python
# 原理：计算 query 和 document 的向量相似度
query_emb = model.encode("年假有几天？")
doc_embs = model.encode(["年假为 15 天", "病假为 10 天"])

scores = [cosine_similarity(query_emb, doc_emb) for doc_emb in doc_embs]
# [0.92, 0.45]  ← "年假为 15 天"相似度最高
```

**优点**：
- 语义理解强："休假"能匹配到"年假"
- 换说法也能找到："请假政策"能匹配到"年假制度"

**缺点**：
- 专有名词弱："GPT-4o"可能匹配不到"GPT-4o-mini"
- 短文本效果差：单个词的向量语义不明确

### 1.2 Sparse 检索（BM25）

```python
from rank_bm25 import BM25Okapi

corpus = ["年假为 15 天", "病假为 10 天"]
tokenized_corpus = [doc.split() for doc in corpus]
bm25 = BM25Okapi(tokenized_corpus)

query = "年假有几天？"
scores = bm25.get_scores(query.split())
# [2.5, 0.0]  ← "年假为 15 天"得分最高
```

**优点**：
- 精确匹配强："GPT-4o"能精确匹配到"GPT-4o"
- 专有名词准确：公司名、产品名、人名

**缺点**：
- 语义理解弱："休假"匹配不到"年假"
- 换说法失效："请假政策"匹配不到"年假制度"

### 1.3 Hybrid 检索（混合检索）

```python
# 步骤 1：分别检索
dense_results = vector_search(query, top_k=20)   # 向量检索 Top 20
sparse_results = bm25_search(query, top_k=20)    # BM25 检索 Top 20

# 步骤 2：融合排序（RRF - Reciprocal Rank Fusion）
def rrf_merge(dense_results, sparse_results, k=60):
    scores = {}
    for rank, doc_id in enumerate(dense_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    for rank, doc_id in enumerate(sparse_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

final_results = rrf_merge(dense_results, sparse_results)
```

**为什么用 Hybrid**：
```
场景 1：用户问"GPT-4o 的价格"
  - Dense：可能匹配到"GPT-4 的价格"（语义相近但不对）
  - Sparse：精确匹配"GPT-4o"
  - Hybrid：✅ 两者结合，既有语义理解又有精确匹配

场景 2：用户问"请假政策"
  - Dense：✅ 能匹配到"年假制度"
  - Sparse：匹配不到（没有"请假"这个词）
  - Hybrid：✅ Dense 兜底

结论：Hybrid 取长补短，召回率最高
```

---

## 2. Rerank（重排序）

```
问题：检索 Top 20，但只需要 Top 5，怎么选？

方案 1：直接取 Top 5
  - 问题：可能不是最相关的 5 个

方案 2：Rerank（精排）
  - 用更强的模型（如 Cross-Encoder）重新排序
  - 类比：海选 20 人 → 复试精选 5 人
```

### Rerank 原理

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("BAAI/bge-reranker-large")

# 粗排：检索 Top 20
candidates = vector_search(query, top_k=20)

# 精排：用 Cross-Encoder 重新打分
pairs = [[query, doc] for doc in candidates]
scores = reranker.predict(pairs)

# 返回 Top 5
top_5 = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)[:5]
```

**为什么 Rerank 更准**：
```
Bi-Encoder（向量检索）：
  - query 和 doc 分别编码，计算相似度
  - 快但不够准（没有交互）

Cross-Encoder（Rerank）：
  - query 和 doc 拼接后一起编码
  - 慢但更准（有交互，能理解上下文）

策略：
  - 粗排用 Bi-Encoder（快速筛选 Top 20）
  - 精排用 Cross-Encoder（精确选出 Top 5）
```

---

## 3. 完整 RAG 实战代码

```python
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI

model = SentenceTransformer("BAAI/bge-large-zh-v1.5")
llm_client = OpenAI(api_key="your-key")

class SimpleRAG:
    def __init__(self):
        self.chunks = []
        self.embeddings = []

    def index(self, documents: list[str]):
        self.chunks = documents
        self.embeddings = model.encode(documents)

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        query_emb = model.encode([query])[0]
        scores = [
            np.dot(query_emb, chunk_emb) /
            (np.linalg.norm(query_emb) * np.linalg.norm(chunk_emb))
            for chunk_emb in self.embeddings
        ]
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [self.chunks[i] for i in top_indices]

    def generate(self, query: str) -> str:
        relevant_chunks = self.retrieve(query)
        context = "\n\n".join(relevant_chunks)
        
        prompt = f"""你是企业知识库助手，请严格基于以下参考资料回答问题。
如果参考资料中没有相关信息，请明确说"根据现有资料，无法回答此问题"。

参考资料：
{context}

用户问题：{query}

请基于参考资料给出准确、简洁的回答。"""
        
        response = llm_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

rag = SimpleRAG()
rag.index([
    "年假为 15 天，入职满一年后生效。",
    "病假为 10 天，需提供医院证明。",
    "事假不超过 5 天，需提前申请。"
])

answer = rag.generate("年假有几天？")
print(answer)
```

---

## 4. 面试考点汇总

### 问法 1："Dense、Sparse、Hybrid 的区别和适用场景？"

**标准答案**：
> "Dense 是向量语义匹配，擅长语义理解但专有名词弱；Sparse 是 BM25 关键词匹配，擅长精确匹配但语义理解弱；Hybrid 结合两者，用 RRF 融合排序，取长补短，召回率最高，是生产环境首选。"

### 问法 2："为什么要用 Rerank？"

**标准答案**：
> "粗排（Bi-Encoder）快但不够准，精排（Cross-Encoder）慢但更准。策略是先用 Bi-Encoder 检索 Top 20，再用 Cross-Encoder 精排选出 Top 5。类比海选 20 人再复试精选 5 人。Cross-Encoder 把 query 和 doc 拼接后一起编码，有交互，能更准确理解相关性。"

### 问法 3："RAG 效果不好怎么排查？"

**排查流程**：
```
1. 检索阶段问题？
   - 打印检索到的文档块，看是否相关
   - 不相关 → 调整 chunk_size、换 Embedding 模型、用 Hybrid

2. 生成阶段问题？
   - 检索到的文档是对的，但回答不对
   - 检查 Prompt 设计，是否明确要求基于文档回答
   - 检查 context 长度是否超出模型窗口

3. 分块问题？
   - 答案被切断在两个 chunk 之间
   - 增大 chunk_overlap
```

**加分项**：
- 能说出 RRF 融合算法的公式
- 能说出 Bi-Encoder 和 Cross-Encoder 的区别
- 能说出 MMR（最大边际相关性）去重策略

---

## 5. 真实踩坑经历

**坑 1：只用 Dense 检索，专有名词匹配不上**
> 用户问"GPT-4o 的价格"，Dense 检索匹配到"GPT-4 的价格"（语义相近但不对）。改成 Hybrid 后，Sparse 精确匹配"GPT-4o"，问题解决。

**坑 2：Rerank 用在粗排，速度慢到无法接受**
> 一开始对所有文档（10 万条）都用 Cross-Encoder 打分，每次查询要 30 秒。改成先 Bi-Encoder 粗排 Top 20，再 Cross-Encoder 精排，速度降到 2 秒。

**坑 3：检索到的文档太多，超出 LLM 窗口**
> 一开始 top_k=10，拼接后超出 GPT-4 的 128K 窗口，LLM 报错。改成 top_k=3 后解决。生产环境要根据 chunk_size 和模型窗口计算合理的 top_k。

---

## 6. 高级技巧

### 6.1 MMR（最大边际相关性）去重

```python
def mmr_rerank(query_emb, doc_embs, lambda_param=0.5, top_k=5):
    selected = []
    candidates = list(range(len(doc_embs)))
    
    for _ in range(top_k):
        mmr_scores = []
        for i in candidates:
            relevance = cosine_similarity(query_emb, doc_embs[i])
            if selected:
                diversity = max([cosine_similarity(doc_embs[i], doc_embs[j]) 
                                for j in selected])
            else:
                diversity = 0
            mmr_scores.append(lambda_param * relevance - (1 - lambda_param) * diversity)
        
        best_idx = candidates[np.argmax(mmr_scores)]
        selected.append(best_idx)
        candidates.remove(best_idx)
    
    return selected
```

### 6.2 Query 改写

```python
# 用户问题可能表达不清，让 LLM 改写成更适合检索的形式
def rewrite_query(original_query):
    prompt = f"""将以下用户问题改写成更适合检索的关键词查询：
    
原问题：{original_query}
改写后："""
    
    response = llm.chat([{"role": "user", "content": prompt}])
    return response
```

---

**导师寄语**：
> 检索策略是 RAG 的核心，面试官问这个是想看你有没有真正做过生产环境的 RAG。记住：生产环境用 Hybrid（Dense + Sparse），加 Rerank 精排，top_k 根据模型窗口计算。能说清楚这三点，这道题就过了。

**下一步**：Week4 Day5 — RAG 进阶技巧（Query 改写、HyDE、Self-RAG）
