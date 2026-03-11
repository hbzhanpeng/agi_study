# 第 4 周 Day 3 学习总结：Embedding 模型选型 + 向量数据库

> **核心目标：掌握 Embedding 模型和向量数据库的选型策略，能在面试中说清楚选型理由和合规考量。**

---

## 1. 为什么需要 Embedding？

```
问题：计算机怎么理解"年假"和"休假"是相关的？

传统方法（关键词匹配）：
  用户问："休假政策是什么？"
  文档："年假为 15 天"
  结果：匹配不上（"休假" ≠ "年假"）

Embedding 方法（语义匹配）：
  "休假" → [0.2, 0.8, 0.3, ...]  (1024维向量)
  "年假" → [0.3, 0.7, 0.4, ...]
  余弦相似度：0.92（非常相似！）
  结果：能匹配上
```

**Embedding 的本质**：把文本映射到高维向量空间，语义相近的文本在空间中距离近。

---

## 2. Embedding 模型选型（面试必背）

| 模型 | 中文效果 | 维度 | 成本 | 适用场景 |
|------|---------|------|------|---------|
| **BGE-large-zh** | ✅ 最强 | 1024 | 免费开源 | **中文场景首选** |
| text-embedding-3-small | 好 | 1536 | 付费 | 快速上线 |
| text-embedding-3-large | 很好 | 3072 | 付费（贵） | 高质量要求 |
| bge-m3 | 多语言强 | 1024 | 免费开源 | 中英混合 |
| M3E | 很好 | 768 | 免费开源 | 轻量中文 |

### 选型决策树

```
中文为主？
  → BGE-large-zh（MTEB 中文榜第一）

多语言混合？
  → bge-m3（支持 100+ 语言）

快速上线，不想部署？
  → OpenAI text-embedding-3-small

追求极致效果？
  → text-embedding-3-large（但贵 10 倍）
```

### 代码示例

```python
from sentence_transformers import SentenceTransformer

# 本地部署（推荐）
model = SentenceTransformer("BAAI/bge-large-zh-v1.5")
embeddings = model.encode(["年假政策", "休假制度"])

# OpenAI API
from openai import OpenAI
client = OpenAI(api_key="your-key")
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=["年假政策", "休假制度"]
)
embeddings = [data.embedding for data in response.data]
```

---

## 3. 向量数据库选型

| 数据库 | 类比 | 适用场景 | 特点 |
|--------|------|---------|------|
| **Chroma** | SQLite | 本地开发、快速原型 | 零配置，内存/本地文件 |
| **Milvus** | MySQL | 生产环境、大规模 | 高性能，支持亿级向量 |
| Pinecone | AWS RDS | 快速上线（⚠️数据出境） | 托管服务，无需运维 |
| FAISS | 内存数组 | 离线实验 | Meta 开源，纯内存 |
| Weaviate | PostgreSQL | 生产环境 | 支持混合检索 |

### 选型决策树

```
本地开发/原型验证？
  → Chroma（pip install chromadb，3 行代码跑起来）

生产环境，数据量 < 100 万？
  → Chroma 持久化模式

生产环境，数据量 > 100 万？
  → Milvus（支持分布式，亿级向量）

敏感行业（金融/政务/医疗）？
  → ❌ 排除 Pinecone（数据存海外）
  → ✅ Milvus 私有化部署

快速上线，不想运维？
  → Pinecone（但要确认数据合规）
```

---

## 4. 索引算法对比

| 算法 | 原理 | 速度 | 精度 | 适用场景 |
|------|------|------|------|---------|
| **HNSW** | 分层图结构 | ✅ 快 | ✅ 高 | **最常用，通用场景** |
| IVF | 倒排索引 | 中 | 中 | 超大数据集（亿级） |
| PQ | 乘积量化 | 快 | 低 | 内存受限场景 |
| Flat | 暴力搜索 | 慢 | ✅ 100% | 小数据集（< 1 万） |

**HNSW（Hierarchical Navigable Small World）**：
```
原理：构建多层图，每层是一个小世界网络
查询：从顶层快速定位到大致区域，逐层下降精确搜索

优点：速度快（毫秒级），精度高（> 95%）
缺点：内存占用大（需要存图结构）

推荐：生产环境首选
```

---

## 5. 完整代码示例

### 5.1 Chroma（本地开发）

```python
import chromadb
from chromadb.utils import embedding_functions

client = chromadb.Client()
collection = client.create_collection(
    name="knowledge_base",
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-large-zh-v1.5"
    )
)

collection.add(
    documents=["年假为 15 天", "病假为 10 天"],
    ids=["doc1", "doc2"]
)

results = collection.query(
    query_texts=["休假政策"],
    n_results=2
)
print(results["documents"])
```

### 5.2 Milvus（生产环境）

```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

connections.connect("default", host="localhost", port="19530")

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535)
]
schema = CollectionSchema(fields, description="knowledge base")
collection = Collection("kb", schema)

collection.create_index(
    field_name="embedding",
    index_params={"index_type": "HNSW", "metric_type": "COSINE", "params": {"M": 16, "efConstruction": 200}}
)

collection.insert([
    [embedding1, embedding2],
    ["年假为 15 天", "病假为 10 天"]
])

collection.load()
results = collection.search(
    data=[query_embedding],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"ef": 64}},
    limit=2
)
```

---

## 6. 面试考点汇总

### 问法 1："Embedding 模型怎么选？"

**标准答案**：
> "根据语言和场景：中文场景首选 BGE-large-zh（MTEB 中文榜第一，免费开源）；多语言混合用 bge-m3；快速上线用 OpenAI text-embedding-3-small。最重要的是在自己的数据集上 benchmark，不要只看排行榜。"

### 问法 2："向量数据库怎么选？"

**标准答案**：
> "开发阶段用 Chroma（零配置，3 行代码跑起来）；生产环境数据量小用 Chroma 持久化，数据量大用 Milvus（支持亿级向量）。敏感行业必须排除 Pinecone（数据存海外），用 Milvus 私有化部署。"

### 问法 3："HNSW 索引的原理是什么？"

**标准答案**：
> "HNSW 是分层图结构，每层是一个小世界网络。查询时从顶层快速定位到大致区域，逐层下降精确搜索。优点是速度快（毫秒级）且精度高（> 95%），是生产环境首选。缺点是内存占用大，需要存储图结构。"

**加分项**：
- 能说出"在自己数据集上 benchmark"的重要性
- 能说出数据合规的考量（敏感行业不能用 Pinecone）
- 能说出 HNSW 的参数调优（M、efConstruction）

---

## 7. 真实踩坑经历

**坑 1：索引和检索用了不同的 Embedding 模型**
> 索引时用 BGE-large-zh，检索时误用了 text-embedding-3-small，导致向量空间不一致，检索结果全是乱的。索引和检索必须用同一个 Embedding 模型！

**坑 2：Pinecone 数据合规问题**
> 给金融客户做项目，一开始用 Pinecone（方便），后来客户审计发现数据存在美国，不符合数据不出境要求，紧急切换到 Milvus 私有化部署。敏感行业一定要提前确认合规要求。

**坑 3：HNSW 参数没调优，召回率低**
> 一开始用默认参数，召回率只有 80%。后来调大 `ef`（查询时的候选集大小）从 10 到 64，召回率提升到 95%。HNSW 的 `ef` 参数对召回率影响很大。

**坑 4：向量维度不匹配**
> 用 BGE-large-zh（1024 维）生成向量，但 Milvus collection 定义成 768 维，插入时报错。向量维度必须和 Embedding 模型输出维度一致。

---

## 8. 高级技巧

### 8.1 混合检索（Hybrid Search）

```python
# 向量检索 + 关键词检索
vector_results = collection.search(query_embedding, top_k=10)
keyword_results = bm25_search(query_text, top_k=10)

# 融合排序（RRF - Reciprocal Rank Fusion）
final_results = rrf_merge(vector_results, keyword_results)
```

### 8.2 向量压缩（节省存储）

```python
# PQ（乘积量化）压缩
collection.create_index(
    field_name="embedding",
    index_params={
        "index_type": "IVF_PQ",
        "metric_type": "COSINE",
        "params": {"nlist": 128, "m": 8}  # m=8 压缩到原来的 1/8
    }
)
```

---

**导师寄语**：
> Embedding 和向量数据库是 RAG 的核心基础设施，选型错了后面全白搭。记住：中文用 BGE-large-zh，开发用 Chroma，生产用 Milvus，敏感行业不能用 Pinecone。能说清楚这几点，这道题就过了。

**下一步**：Week4 Day4 — 检索策略（Dense/Sparse/Hybrid Search + Rerank）
