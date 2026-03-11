# 第 4 周 Day 2 学习总结：文档处理流水线与 Chunking 策略

> **核心目标：深入理解文档分块策略的原理和参数选择，能在面试中说清楚为什么这样设计。**

---

## 1. 为什么要分块（Chunking）？

```
问题：为什么不能把整本书直接塞给 LLM？

原因 1：上下文窗口限制
  - GPT-4：128K tokens ≈ 20 万字
  - 一本书可能有 50 万字
  - 超出窗口就无法处理

原因 2：注意力分散（Lost in the Middle）
  - 研究表明：LLM 对开头和结尾的内容注意力高
  - 中间部分容易被"忽略"
  - 文档越长，关键信息越容易丢失

原因 3：检索精准度
  - 整本书作为一个向量，语义太模糊
  - 无法精准匹配用户问题
  - 分块后每块语义更聚焦，检索更准确

原因 4：成本
  - Token 按量计费
  - 每次查询都塞整本书，成本爆炸
```

---

## 2. 三种 Chunking 策略

| 策略 | 原理 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|---------|
| **固定大小** | 每 N 字切一块 | 简单、快速 | 可能切断语义 | 格式统一的文档 |
| **递归分块 ✅** | 按标题→段落→句子→字符逐层切 | 保持语义完整 | 略复杂 | **最常用，通用场景** |
| **语义分块** | Embedding 判断语义边界 | 最智能 | 慢且贵 | 高质量要求场景 |

### 2.1 固定大小分块

```python
def fixed_size_chunking(text: str, chunk_size: int = 500) -> list[str]:
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks

# 问题：可能切断句子
text = "...年假为15天。入职满一年后生效。具体请咨询HR..."
# 切成：
# Chunk 1: "...年假为15天。入职满一"
# Chunk 2: "年后生效。具体请咨询HR..."
# ❌ "入职满一年后生效"被切断了！
```

### 2.2 递归分块（LangChain 默认，最常用）

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # 每块最大字符数
    chunk_overlap=50,    # 相邻块重叠字符数
    separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    # 优先级：段落 > 换行 > 句子 > 空格 > 字符
)

chunks = splitter.split_text(text)
```

**工作原理**：
```
1. 先尝试按 "\n\n"（段落）切分
2. 如果切出的块 > chunk_size，再按 "\n"（换行）切
3. 还是太大，按 "。"（句子）切
4. 最后才按字符强制切

结果：尽可能保持语义完整
```

### 2.3 语义分块

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-large-zh-v1.5")

def semantic_chunking(sentences: list[str], threshold: float = 0.5):
    chunks = []
    current_chunk = [sentences[0]]
    
    for i in range(1, len(sentences)):
        prev_emb = model.encode(sentences[i-1])
        curr_emb = model.encode(sentences[i])
        similarity = cosine_similarity(prev_emb, curr_emb)
        
        if similarity < threshold:  # 语义跳跃，切分
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentences[i]]
        else:
            current_chunk.append(sentences[i])
    
    chunks.append(" ".join(current_chunk))
    return chunks
```

**优点**：按语义边界切分，最智能
**缺点**：每个句子都要 Embedding，慢且贵

---

## 3. Chunk 参数选择（面试必答）

### 3.1 chunk_size（块大小）

| 大小 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| 200-300 字 | 检索精准 | 丢失上下文 | 短问答、FAQ |
| **500-1000 字 ✅** | 平衡 | - | **通用场景** |
| 1500-2000 字 | 上下文完整 | 检索不精准 | 长文档分析 |

**选择原则**：
```
文档类型决定 chunk_size：
- FAQ/问答对 → 200-300 字（每个问答是独立的）
- 技术文档 → 500-1000 字（需要一定上下文）
- 法律合同 → 1000-2000 字（条款之间有关联）
```

### 3.2 chunk_overlap（重叠大小）

```
为什么需要重叠？

场景：
"...年假为15天。入职满一年后生效。具体请咨询HR..."

不重叠：
Chunk 1: "...年假为15天。"
Chunk 2: "入职满一年后生效。..."
问题：用户问"年假几天？"，检索到 Chunk 1，但没有"入职满一年后生效"的条件

重叠 50 字：
Chunk 1: "...年假为15天。入职满一年后生效。"
Chunk 2: "入职满一年后生效。具体请咨询HR..."
✅ Chunk 1 包含完整信息
```

**推荐值**：
```
chunk_overlap = chunk_size × 10-20%

chunk_size=500 → overlap=50-100
chunk_size=1000 → overlap=100-200
```

---

## 4. 文档解析流水线

```python
from langchain.document_loaders import (
    PyPDFLoader,      # PDF
    Docx2txtLoader,   # Word
    WebBaseLoader,    # 网页
    CSVLoader,        # CSV
)
from langchain.text_splitter import RecursiveCharacterTextSplitter

def process_document(file_path: str):
    # 步骤 1：加载文档
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError("不支持的文件格式")
    
    documents = loader.load()
    
    # 步骤 2：分块
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    )
    chunks = splitter.split_documents(documents)
    
    # 步骤 3：添加元数据
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
        chunk.metadata["source"] = file_path
    
    return chunks
```

---

## 5. 面试考点汇总

### 问法 1："Chunk 大小怎么选？"

**标准答案**：
> "根据文档类型和业务场景：FAQ 类短问答用 200-300 字，技术文档用 500-1000 字，法律合同用 1000-2000 字。通用场景推荐 500-1000 字，平衡检索精准度和上下文完整性。最好在自己的数据集上 A/B 测试，用评估指标（Recall/Precision）选最优值。"

### 问法 2："为什么需要 chunk_overlap？"

**标准答案**：
> "防止关键信息被切断在两个 chunk 边界。比如'年假 15 天，入职满一年后生效'，如果不重叠，可能'年假 15 天'在 Chunk 1，'入职满一年后生效'在 Chunk 2，检索时只找到 Chunk 1，丢失了条件。重叠 10-20% 可以让边界信息在两个 chunk 中都出现。"

### 问法 3："递归分块和固定大小分块的区别？"

**标准答案**：
> "固定大小按字符数强制切分，可能切断句子和段落，破坏语义。递归分块按优先级（段落→句子→字符）逐层切分，尽可能保持语义完整。生产环境推荐递归分块，LangChain 的 RecursiveCharacterTextSplitter 是最常用的实现。"

**加分项**：
- 能说出"Lost in the Middle"问题
- 能说出语义分块的原理和成本
- 能说出 A/B 测试选参数的方法

---

## 6. 真实踩坑经历

**坑 1：chunk_size 设太小，答案不完整**
> 一开始设 200 字，结果"年假 15 天，入职满一年后生效"被切成两块，检索时只找到"年假 15 天"，用户以为入职就有年假，导致理解错误。调大到 500 后解决。

**坑 2：没有 chunk_overlap，跨块信息丢失**
> 两个相邻 chunk 的边界处有关键信息，没有重叠导致检索时两块都不完整。加了 50 字重叠后，边界信息不再丢失。

**坑 3：PDF 表格解析失败**
> 用 PyPDFLoader 解析带表格的 PDF，表格内容全乱了。后来改用 `unstructured` 库的 `partition_pdf()`，支持表格识别，解析质量大幅提升。

**坑 4：中文分词边界问题**
> 用英文的 separators `["\n\n", "\n", ". ", " "]`，中文句子切不开。改成 `["。", "！", "？"]` 后解决。

---

## 7. 高级技巧

### 7.1 动态 chunk_size

```python
def adaptive_chunking(text: str, base_size: int = 500):
    if "法律" in text or "合同" in text:
        chunk_size = 1500  # 法律文档需要更多上下文
    elif "FAQ" in text:
        chunk_size = 300   # FAQ 每条独立
    else:
        chunk_size = base_size
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size)
    return splitter.split_text(text)
```

### 7.2 保留文档结构

```python
from langchain.text_splitter import MarkdownHeaderTextSplitter

splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
)

# 按 Markdown 标题层级切分，保留结构信息
chunks = splitter.split_text(markdown_text)
```

---

**导师寄语**：
> Chunking 是 RAG 的第一道关卡，参数选不好，后面检索再准也没用。记住：chunk_size 根据文档类型选（500-1000 通用），chunk_overlap 设 10-20%，用递归分块保持语义完整。能说清楚这三点，这道题就过了。

**下一步**：Week4 Day3 — Embedding 模型选型 + 向量数据库
