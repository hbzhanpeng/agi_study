# AGI 开发核心知识复习文档
 
---
 
## 一、RAG 系统
 
### 为什么需要 RAG？
LLM 的上下文窗口有限（如 128k token），海量文档无法全部塞入。RAG 的核心思路：
```
分片 → 向量化 → 存储 → 检索最相关的片段 → 塞给 LLM
```
 
### Chunk 分片
```python
# 错误做法：硬切，破坏语义
chunks = text.split("\n\n")
 
# 正确做法：overlap 分片
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
step = CHUNK_SIZE - CHUNK_OVERLAP
chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), step)]
```
 
**为什么需要 overlap？** 硬切会把一句话切成两半，被切断的词向量化后语义不完整，检索相似度下降。
 
### Embedding 和向量检索
- Embedding：把文字映射到高维向量空间，语义相近的向量距离更近
- ChromaDB 默认用 **L2 距离**，距离越小越相关（不是越大）
- 中文场景推荐 BGE 模型，比 OpenAI embedding 更适合中文
 
### HyDE（Hypothetical Document Embeddings）
 
**问题：** 用户问题是疑问句，知识库存的是陈述句，两者语义空间天然有距离。
 
**解决：** 先让 LLM 生成一个假设答案（陈述句），用答案去检索答案，语义更匹配。
 
```
用户问题（疑问句）→ LLM 生成假设答案（陈述句）→ 向量化 → 检索
```
 
**效果：** 准确率从 75% 提升到 87.5%
 
### 问题改写
 
**问题：** 多轮对话里用户说「那怎么解决呢」，「那」指什么不清楚。
 
**解决：** 结合 history 把模糊问题补全成完整问题，再去检索。
 
### RAG 评估指标
- **检索准确率**：检索到的内容是否相关
- **回答忠实度**：LLM 是否基于检索内容回答，没有编造
- **回答相关性**：是否真正回答了问题
 
---
 
## 二、Agent 系统
 
### Agent vs RAG 的本质区别
- **RAG**：硬编码流水线，固定步骤，写死的
- **Agent**：LLM 自主决策，看到用户意图后自己判断用哪个工具、什么顺序
 
### Function Calling 工作原理
```python
# 1. 定义工具描述
tools = [{
    "type": "function",
    "function": {
        "name": "ask_rag",
        "description": "查询个人知识库",
        "parameters": {...}
    }
}]
 
# 2. LLM 返回工具调用指令（不是文字）
message = {"tool_calls": [{"function": {"name": "ask_rag", "arguments": "{...}"}}]}
 
# 3. 执行工具，把结果加入 history
# 4. LLM 基于工具结果生成最终答案
```
 
### ReAct 循环
```
思考（LLM决定用什么工具）
  ↓
行动（执行工具）
  ↓
观察（工具结果加入history）
  ↓
再思考（LLM决定下一步）
  ↓
返回最终答案
```
 
### Agent 可靠性
```python
# 工具失败处理
try:
    result = execute_tool(tool_name, tool_args)
except Exception as e:
    result = f"工具调用失败: {e}，请重试或换一种方式"
# 把错误信息反馈给 LLM，让它自己决定下一步
 
# 防死循环
max_steps = 5
 
# 未知工具处理
result = f"工具 '{tool_name}' 不存在，可用工具: ask_rag, add_note"
 
# 行为边界（system prompt）
"知识库有内容才回答，没有则告知用户，不要用自己的知识补充"
```
 
---
 
## 三、Transformer 原理
 
### Self-Attention
```python
def self_attention(Q, K, V):
    d_k = Q.shape[-1]
    scores = Q @ K.T / np.sqrt(d_k)  # 点积 + 缩放
    weights = softmax(scores)          # 归一化
    return weights @ V                 # 加权求和
```
 
**Q、K、V 是什么：**
- Q（Query）：当前词在问「谁和我相关？」
- K（Key）：每个词在说「我是什么」
- V（Value）：每个词真正要贡献的信息
 
**为什么除以 √d_k？**
向量维度越高，点积值越大。点积太大经过 Softmax 后注意力集中在一个词上，其他词信息丢失。除以 √d_k 把点积缩放回合理范围，让每个词都能贡献信息。
 
### Multi-Head Attention
```python
def multi_head_attention(Q, K, V, num_heads=2):
    d_k = Q.shape[-1] // num_heads
    heads = []
    for i in range(num_heads):
        q_i = Q[:, i*d_k:(i+1)*d_k]
        k_i = K[:, i*d_k:(i+1)*d_k]
        v_i = V[:, i*d_k:(i+1)*d_k]
        heads.append(self_attention(q_i, k_i, v_i))
    return np.concatenate(heads, axis=-1)
```
 
**为什么需要多头？** 单头只能学一种关注模式，多头让每个 head 从不同角度理解语义（主谓关系、动宾关系等）。
 
### 位置编码
 
Self-Attention 本身没有顺序感知，「我喜欢吃苹果」和「苹果吃喜欢我」算出来一样。
 
位置编码在词向量上加上位置信息：
```
PE(pos, 2i)   = sin(pos / 10000^(2i/d))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d))
```
 
sin/cos 值域 [-1,1]，不会随序列长度无限增大。
 
### GPT vs BERT
 
| | GPT | BERT |
|---|---|---|
| 注意力方向 | 单向（只看左边）| 双向（看整句）|
| 训练方式 | 预测下一个词 | 完形填空 |
| 适合任务 | 文本生成 | 文本理解 |
| 代表应用 | ChatGPT | Embedding模型 |
 
**你的 BGE 模型是 BERT 系列**，因为 embedding 需要理解整句话语义，双向注意力效果更好。
 
---
 
## 四、KV Cache
 
**问题：** LLM 生成每个 token 都需要看所有历史 token，重复计算。
 
**解决：** 把历史 token 的 K 和 V 缓存起来，每次只计算新 token 的 Q。
 
**为什么只缓存 K 和 V，不缓存 Q？**
Q 是当前 token 的表示，每次都不同；K/V 是历史 token 的，可以复用。
 
**两个阶段：**
- **prefill**：第一个 token，计算所有输入的 K/V，没有缓存，慢
- **decode**：后续 token，K/V 已缓存，只算新 token 的 Q，快
 
这就是为什么流式输出第一个字慢，后面越来越快。
 
**代价：** 显存占用随序列长度增长，长对话会越来越慢。
 
---
 
## 五、系统设计：生产级 RAG
 
### 检索性能
- 暴力检索（Brute Force）：和所有向量算距离，10万条很慢
- **HNSW 索引**：近似最近邻，只算可能相关的，ChromaDB 默认使用
 
### 索引稳定性
```python
# 批量索引 + 断点续传
BATCH_SIZE = 100
for i in range(0, len(chunks), BATCH_SIZE):
    batch = chunks[i:i+BATCH_SIZE]
    embeddings = get_embedding(batch)
    collection.add(...)
```
 
### 多租户隔离
 
| 方案 | 优势 | 劣势 | 适用场景 |
|---|---|---|---|
| 每个租户一个 collection | 完全隔离，安全 | collection 数量多 | 租户少，数据量大 |
| metadata 过滤 | 管理简单 | 检索性能随数据量下降 | 租户多，数据量小 |
 
### 语义缓存
```
问题 → 向量化 → 在缓存库检索
  距离小（相似度高）→ 命中，直接返回
  距离大（相似度低）→ 未命中，调用 LLM，存入缓存
```
 
### 监控指标
- 错误率（系统可用性）
- 缓存命中率（成本优化）
- 知识库未命中率（覆盖率）
- 幻觉率（回答质量）
- P99 延迟（响应时间）
 
---
 
## 六、模型微调
 
### 什么时候用微调 vs RAG vs Prompt
 
| 方案 | 适用场景 |
|---|---|
| Prompt Engineering | 需求经常变化，数据量少，快速验证 |
| RAG | 有大量外部知识，知识经常更新 |
| 微调 | 需要特定输出格式，通用模型效果不够，推理成本敏感 |
 
### LoRA 原理
 
不直接修改原始权重 W，而是在旁边加两个小矩阵：
```
原始：y = Wx
LoRA：y = Wx + BAx
 
W: 4096×4096 = 1600万参数（冻结）
A: 4096×8   = 3万参数（训练）
B: 8×4096   = 3万参数（训练）
参数量减少 99.6%
```
 
**秩 r（rank）：** 上面的 8，越大表达能力越强，显存越高，一般选 4/8/16/32。
 
### QLoRA
在 LoRA 基础上把原始权重量化成 int4，显存再减少 75%。7B 模型微调只需要 6-8GB 显存。
 
### 训练数据格式（Alpaca）
```json
{
    "instruction": "RAG里results忘记传给LLM怎么办",
    "input": "",
    "output": "【问题】...\n【原因】...\n【解决】..."
}
```
 
---
 
## 七、常见面试题速查
 
**Q: Self-Attention 怎么计算？**
Q 和 K 点积算相关度，除以 √d_k 防止梯度消失，Softmax 归一化，乘以 V 加权求和。
 
**Q: 为什么要 Multi-Head？**
单头只能学一种关注模式，多头把向量拆成多份，每份学不同的语义关系，最后拼接得到更丰富的表示。
 
**Q: GPT 和 BERT 的区别？**
GPT 单向，只看左边，适合生成；BERT 双向，看整句，适合理解。
 
**Q: KV Cache 是什么？**
缓存历史 token 的 K 和 V，decode 阶段不重复计算，加速推理。代价是显存随序列长度增长。
 
**Q: RAG 效果不好怎么排查？**
1. 检索问题：相似度分数、chunk 大小、分片策略
2. 检索准确率：加 HyDE、问题改写
3. 生成问题：prompt 格式、context 质量
 
**Q: LoRA 原理？**
不更新原始权重，在旁边加两个低秩矩阵 A 和 B，只训练 A 和 B，参数量减少 99% 以上。
 
**Q: 什么时候用微调？**
需要特定输出格式、风格稳定、通用模型效果不够、推理成本敏感。
 
**Q: Agent 和 RAG 的本质区别？**
RAG 是写死的流水线，Agent 是 LLM 自主决策，根据用户意图决定用哪个工具、什么顺序。
 
**Q: 为什么需要位置编码？**
Self-Attention 本身没有顺序感知，相同的词不管在哪个位置计算结果一样。位置编码给每个词加上位置信息，让模型能区分词序。
 
**Q: 设计一个生产级 RAG 系统？**
HNSW 索引加速检索 → 批量索引+断点续传保证稳定性 → collection/metadata 实现多租户隔离 → 语义缓存降低成本 → 监控错误率/命中率/延迟。
 
---
 
## 八、项目量化数据（面试用）
 
- 知识库评估数据集：9 条
- 无 HyDE 准确率：75%
- 有 HyDE 准确率：87.5%
- HyDE 提升：**12.5 个百分点**
- Agent 最大步数限制：5 步（防死循环）
- 历史摘要触发条件：超过 10 轮对话