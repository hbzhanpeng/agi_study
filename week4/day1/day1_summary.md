# 第 4 周 Day 1 学习总结：RAG 核心架构

> **核心目标：深入理解 RAG 的三大阶段和每个组件的设计选择，能在面试中画出完整架构图并解释每个决策。**

---

## 1. 为什么需要 RAG？

```
LLM 的两大致命缺陷：

缺陷 1：知识截止
  - GPT-4 训练数据截止 2023 年
  - 不知道你公司的内部文档
  - 不知道昨天发生的新闻

缺陷 2：幻觉（Hallucination）
  - 模型会"一本正经地胡说八道"
  - 无法验证答案来源
  - 在医疗/法律/金融场景是致命问题

RAG 的解法：
  "先搜索相关文档，再基于文档回答"
  - 知识可以实时更新（重新索引即可）
  - 答案有据可查（可以显示来源）
  - 不需要重新训练模型
```

**RAG vs Fine-tuning 选型**：

| 维度 | RAG | Fine-tuning |
|------|-----|-------------|
| 知识更新 | ✅ 实时（重新索引） | ❌ 需重新训练（天/周级） |
| 成本 | ✅ 低（只需向量数据库） | ❌ 高（GPU 训练费用） |
| 可解释性 | ✅ 可溯源（显示来源文档） | ❌ 黑盒 |
| 幻觉控制 | ✅ 基于真实文档 | ❌ 仍可能幻觉 |
| 适合场景 | 知识库问答、文档检索 | 风格迁移、特定领域语言 |

**结论**：90% 的企业知识库场景用 RAG，不用 Fine-tuning。

---

## 2. RAG 三大阶段（面试必画）

```
┌─────────────────────────────────────────────────────┐
│                  阶段 1：Indexing（离线）              │
│                                                     │
│  原始文档                                            │
│  (PDF/Word/HTML)                                    │
│      ↓                                              │
│  文档解析（提取纯文本）                               │
│      ↓                                              │
│  文本分块 Chunking（500-1000字/块，10-20%重叠）        │
│      ↓                                              │
│  Embedding 模型（文本 → 向量）                        │
│      ↓                                              │
│  存入向量数据库（Milvus/Chroma）                      │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  阶段 2：Retrieval（在线）             │
│                                                     │
│  用户提问："年假有几天？"                              │
│      ↓                                              │
│  Query Embedding（问题 → 向量）                       │
│      ↓                                              │
│  向量相似度搜索（余弦相似度）                          │
│      ↓                                              │
│  返回 Top K 相关文档块（K=3~5）                       │
│      ↓                                              │
│  （可选）Rerank 精排                                  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  阶段 3：Generation（在线）            │
│                                                     │
│  [检索到的文档块] + [用户问题]                         │
│      ↓                                              │
│  构建 RAG Prompt                                     │
│      ↓                                              │
│  LLM 生成回答                                        │
│      ↓                                              │
│  （可选）显示来源文档                                  │
└─────────────────────────────────────────────────────┘
```

---

## 3. 每个组件的设计选择

### 3.1 文档解析

```python
# 不同格式用不同解析器
from langchain.document_loaders import (
    PyPDFLoader,      # PDF
    Docx2txtLoader,   # Word
    WebBaseLoader,    # 网页
    CSVLoader,        # CSV
)

# 注意：PDF 解析是最难的
# 扫描版 PDF → 需要 OCR（pytesseract）
# 带表格的 PDF → 需要专门的表格提取
# 推荐：unstructured 库，支持多格式统一解析
```

### 3.2 文本分块（Chunking）

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # 每块最大字符数
    chunk_overlap=50,    # 相邻块重叠字符数（防止信息丢失）
    separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    # 优先按段落切，其次按句子，最后按字符
)
```

**参数选择原则**：
- `chunk_size`：500-1000 字。太小丢上下文，太大检索不精准
- `chunk_overlap`：chunk_size 的 10-20%。防止答案跨块被切断

### 3.3 Embedding 模型

| 模型 | 中文效果 | 成本 | 推荐场景 |
|------|---------|------|---------|
| BGE-large-zh | ✅ 最强 | 免费开源 | 中文场景首选 |
| text-embedding-3-small | 好 | 付费 | 快速上线 |
| bge-m3 | 多语言强 | 免费开源 | 中英混合 |

### 3.4 向量数据库

| 数据库 | 适用场景 | 特点 |
|--------|---------|------|
| Chroma | 本地开发、原型 | 零配置，内存/本地文件 |
| Milvus | 生产环境 | 高性能，支持亿级向量 |
| Pinecone | 快速上线（⚠️数据出境） | 托管服务，无需运维 |
| FAISS | 离线实验 | Meta 开源，纯内存 |

---

## 4. RAG Prompt 设计

```python
RAG_PROMPT = """你是企业知识库助手，请严格基于以下参考资料回答问题。
如果参考资料中没有相关信息，请明确说"根据现有资料，无法回答此问题"，不要编造答案。

参考资料：
{context}

用户问题：{question}

请基于参考资料给出准确、简洁的回答，并在回答末尾注明信息来源（第几篇资料）。"""
```

**关键设计**：
- 明确说"基于参考资料回答"，减少幻觉
- 明确说"没有信息就说没有"，防止编造
- 要求注明来源，增加可信度

---

## 5. 完整代码示例

```python
import numpy as np
from sentence_transformers import SentenceTransformer

class SimpleRAG:
    def __init__(self):
        self.model = SentenceTransformer("BAAI/bge-large-zh-v1.5")
        self.chunks = []
        self.embeddings = []

    def index(self, documents: list[str]):
        self.chunks = documents
        self.embeddings = self.model.encode(documents)

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        query_emb = self.model.encode([query])[0]
        scores = [
            np.dot(query_emb, chunk_emb) /
            (np.linalg.norm(query_emb) * np.linalg.norm(chunk_emb))
            for chunk_emb in self.embeddings
        ]
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [self.chunks[i] for i in top_indices]

    def generate(self, query: str, llm) -> str:
        relevant_chunks = self.retrieve(query)
        context = "\n\n".join(relevant_chunks)
        prompt = RAG_PROMPT.format(context=context, question=query)
        return llm.chat([{"role": "user", "content": prompt}])
```

---

## 6. 面试考点汇总

### 问法 1："画出 RAG 完整架构并解释每个组件的设计选择"

**标准答案**：
> "RAG 分三个阶段：Indexing（离线）、Retrieval（在线）、Generation（在线）。
>
> Indexing：文档解析 → 分块（RecursiveCharacterTextSplitter，500字/块，50字重叠）→ Embedding（中文用 BGE-large-zh）→ 存入向量数据库（开发用 Chroma，生产用 Milvus）。
>
> Retrieval：用户问题 Embedding → 余弦相似度搜索 → 返回 Top K 文档块 → 可选 Rerank 精排。
>
> Generation：把检索到的文档块和用户问题拼成 Prompt → LLM 生成回答 → 显示来源。"

### 问法 2："RAG 效果不好怎么排查？"

**排查流程**：
```
1. 检索阶段问题？
   - 打印检索到的文档块，看是否相关
   - 不相关 → 调整 chunk_size、换 Embedding 模型、用混合检索

2. 生成阶段问题？
   - 检索到的文档是对的，但回答不对
   - 检查 Prompt 设计，是否明确要求基于文档回答
   - 检查 context 长度是否超出模型窗口

3. 分块问题？
   - 答案被切断在两个 chunk 之间
   - 增大 chunk_overlap
```

### 问法 3："RAG 和 Fine-tuning 怎么选？"

**标准答案**：
> "知识需要实时更新、需要溯源验证、成本敏感 → 用 RAG。需要改变模型的输出风格、特定领域的语言习惯、任务格式固定 → 用 Fine-tuning。大多数企业知识库场景用 RAG，Fine-tuning 用于垂直领域的语言风格迁移。"

**加分项**：
- 能说出 RAG 的局限（检索不到的信息无法回答）
- 能说出 RAG + Fine-tuning 结合使用的场景

---

## 7. 真实踩坑经历

**坑 1：chunk_size 设太小，答案被切断**
> 一开始 chunk_size=200，结果"年假 15 天，入职满一年后生效"被切成两块，检索时只找到"年假 15 天"，没找到"入职满一年后生效"，导致回答不完整。调大到 500 后解决。

**坑 2：没有 chunk_overlap，跨块信息丢失**
> 两个相邻 chunk 的边界处有关键信息，没有重叠导致检索时两块都不完整。加了 50 字重叠后，边界信息不再丢失。

**坑 3：Embedding 模型和检索模型不匹配**
> 索引时用 BGE-large-zh，检索时误用了 text-embedding-3-small，导致向量空间不一致，检索结果全是乱的。索引和检索必须用同一个 Embedding 模型！

---

**导师寄语**：
> RAG 是面试重灾区，几乎 100% 会问。记住核心：三个阶段（Indexing/Retrieval/Generation），每个阶段的关键参数（chunk_size/overlap/top_k），以及效果不好时的排查思路。能画出架构图并解释每个设计选择，这道题就满分了。

**下一步**：Week4 Day2 — 文档处理流水线与 Chunking 策略（深入）
