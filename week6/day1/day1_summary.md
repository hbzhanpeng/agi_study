# 第 6 周 Day 1 学习总结：微调 vs Prompt Engineering vs RAG 选型决策树

> **核心目标：掌握三大技术方案的选型决策逻辑，能在面试中画出决策树并解释每个分支的判断依据。这是面试官最爱考的架构设计题（★★★★★）。**

---

## 1. 为什么要学这个？

### 面试中最常见的问题

```
面试官："你要做一个 XX 系统，会用微调、RAG 还是 Prompt Engineering？为什么？"
```

**这道题考察什么**：
- **技术选型能力**：不是只会用一种方案
- **成本意识**：微调很贵，能不用就不用
- **工程思维**：权衡利弊，不追求最新技术

### 真实项目场景

我当年做客服系统时，一开始想用微调（觉得很酷），结果：
- 收集数据花了 2 周
- 训练花了 1 周
- 产品更新后又要重新训练

后来改用 RAG，更新文档 5 分钟搞定。**这就是为什么要学选型决策。**

---

## 2. 三大方案的本质区别

| 方案 | 本质 | 类比前端 | 改变了什么 |
|------|------|---------|-----------|
| **Prompt Engineering** | 改输入 | 改 API 请求参数 | 输入变了，模型不变 |
| **RAG** | 注入外部知识 | 从数据库查数据传给组件 | 动态注入知识，模型不变 |
| **微调** | 改模型参数 | 重新训练神经网络 | 模型本身被改变 |

### 核心理解

```python
# Prompt Engineering
response = llm("请用专业语气回答：" + question)

# RAG
docs = search_db(question)
response = llm(f"根据{docs}回答：{question}")

# 微调
fine_tuned_model = train(base_model, training_data)
response = fine_tuned_model(question)
```

**关键点**：
- Prompt：模型不变，只是换个问法
- RAG：模型不变，但给它提供了新信息
- 微调：模型本身被改变了，"学会"了新知识

---
## 3. Prompt Engineering（提示词工程）

### 核心概念

通过精心设计输入提示词，让模型输出符合预期的结果。

**适用场景**：
- ✅ 通用任务（翻译、摘要、问答）
- ✅ 模型已有相关知识
- ✅ 快速验证想法（0 成本）

**优缺点**：

| 优点 | 缺点 |
|------|------|
| 零成本、零延迟 | 受限于模型原有能力 |
| 灵活调整 | 无法注入新知识 |
| 不需要数据和算力 | 输出不稳定 |

### 代码示例

```python
prompt = """
你是专业的客服助手。请用礼貌、专业的语气回答。

用户问题：{question}

回答格式：
1. 先表示理解
2. 给出解决方案
3. 询问是否还有其他问题
"""

response = llm.generate(prompt.format(question="如何退货？"))
```

### 面试考点

**问**："Prompt Engineering 的局限性是什么？"

**答**：
> "最大局限是无法注入模型不知道的知识。比如公司内部文档、最新产品信息，模型训练时没见过，再怎么优化 Prompt 也答不出来。这时候必须用 RAG 或微调。"

---

## 4. RAG（检索增强生成）

### 核心概念

先从知识库检索相关文档，再把文档和问题一起给模型生成答案。

**架构流程**：

```
用户问题 → Embedding → 向量检索 → Top-K 文档 → 拼接 Prompt → LLM → 答案
```

**适用场景**：
- ✅ 需要实时、准确的外部知识
- ✅ 知识会频繁更新（产品文档、新闻）
- ✅ 需要可追溯性（能标注信息来源）

**优缺点**：

| 优点 | 缺点 |
|------|------|
| 知识实时更新（改文档即可） | 依赖检索质量 |
| 可追溯（显示引用来源） | 增加延迟（检索+生成） |
| 成本低（只需向量数据库） | 上下文长度限制 |
| 减少幻觉（基于真实文档） | - |

### 代码示例

```python
def rag_answer(question: str):
    query_embedding = embed_model.encode(question)
    docs = vector_db.search(query_embedding, top_k=3)
    context = "\n\n".join([doc.content for doc in docs])
    
    prompt = f"""
根据以下文档回答问题：

{context}

问题：{question}

如果文档中没有相关信息，请说"我不知道"。
"""
    return llm.generate(prompt)
```

### 面试考点

**问**："RAG 的缺点是什么？怎么解决？"

**答**：
> "主要三个缺点：1) 检索质量影响答案质量，解决方法是用 Hybrid Search（向量+关键词）和 Rerank；2) 增加延迟，解决方法是异步检索或缓存热门问题；3) 上下文长度限制，解决方法是用 Chunk 策略和摘要。"

---
## 5. 微调（Fine-tuning）

### 核心概念

用特定领域的数据训练模型，让模型"学会"新知识或新能力。

**适用场景**：
- ✅ 需要特定领域的专业能力（医疗、法律）
- ✅ 需要特定的输出风格（代码格式、写作风格）
- ✅ 需要模型"记住"大量知识
- ✅ 对延迟要求高（不能每次都检索）

**优缺点**：

| 优点 | 缺点 |
|------|------|
| 模型真正"学会"了新能力 | 成本高（需要 GPU、数据、时间） |
| 推理时无需额外检索（延迟低） | 知识更新慢（改知识需要重新训练） |
| 可以改变模型行为（风格、格式） | 可能过拟合 |

### 代码示例

```python
from peft import LoraConfig, get_peft_model

config = LoraConfig(
    r=8,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1
)

model = get_peft_model(base_model, config)

trainer = Trainer(
    model=model,
    train_dataset=train_data,
    args=training_args
)

trainer.train()
```

### 面试考点

**问**："什么时候用微调？"

**答**：
> "当知识相对固定、需要模型深度理解、对延迟敏感时用微调。比如医疗诊断（专业知识）、法律文书（特定格式）。但如果知识频繁更新，用 RAG 更合适。"

---

## 6. 选型决策树（面试必背）

### 决策流程

```
问题1: 模型已经会了吗？
  ├─ 会 → Prompt Engineering
  └─ 不会 → 问题2

问题2: 知识会频繁更新吗？
  ├─ 会 → 检查风格需求
  │        ├─ 需要特定风格 + 预算充足 → RAG + 微调
  │        └─ 否则 → RAG
  └─ 不会 → 问题3

问题3: 有预算和数据吗？
  ├─ 有 + 需要特定风格 → 微调
  └─ 否则 → RAG
```

### 典型场景选型

| 场景 | 推荐方案 | 原因 |
|------|---------|------|
| 客服问答 | RAG | 产品信息频繁更新 |
| 代码生成 | Prompt | 模型已有编程能力 |
| 医疗诊断 | 微调 | 需要专业知识，对延迟敏感 |
| 新闻摘要 | RAG | 实时性要求高 |
| 法律文书 | RAG + 微调 | 微调学风格，RAG 提供案例 |

---
## 7. 面试高频问答

### 问题 1

**问**："什么时候用微调，什么时候用 RAG？"

**答**：
> "关键看两点：知识更新频率和成本预算。如果知识频繁更新（如产品文档、新闻），用 RAG，因为改文档比重新训练快得多。如果知识相对固定且需要模型深度理解（如医疗、法律），用微调。成本上，RAG 只需向量数据库，微调需要 GPU 和大量数据。"

### 问题 2

**问**："如果我既要实时知识，又要特定风格，怎么办？"

**答**：
> "用 RAG + 微调组合。微调让模型学会你要的输出风格（比如法律文书格式），RAG 提供实时的案例和法规。推理时，先 RAG 检索相关文档，再用微调后的模型生成符合格式要求的答案。"

### 问题 3

**问**："微调需要多少数据？"

**答**：
> "取决于任务复杂度。简单任务（如改变输出格式）几百条就够；复杂任务（如学习新领域知识）需要几千到几万条。如果数据不够，可以用 Few-shot Prompt 或 RAG 代替。LoRA 这种参数高效方法可以降低数据需求。"

---

## 8. 实战代码

文件路径：`week6/day1/solution_selector.py`

**核心实现**：

```python
def select_solution(req: TaskRequirements) -> Solution:
    if req.needs_external_knowledge:
        if req.knowledge_updates_frequently:
            if req.budget_high and req.needs_specific_style:
                return Solution.RAG_FINETUNE
            else:
                return Solution.RAG
        else:
            if req.budget_high and req.needs_specific_style:
                return Solution.FINETUNE
            else:
                return Solution.PROMPT
    else:
        if req.has_labeled_data and req.needs_specific_style:
            return Solution.FINETUNE
        else:
            return Solution.PROMPT
```

**测试结果**：
```
客服问答: RAG ✓
代码生成: Prompt Engineering ✓
法律文书: RAG + Fine-tuning ✓
医疗诊断: Fine-tuning ✓
```

---

## 9. 真实踩坑经历

**事故 1：盲目微调导致成本爆炸**
> 刚入行时，遇到任何问题都想微调。做客服系统，花了 2 周收集数据、1 周训练，结果产品更新后又要重新训练。后来改用 RAG，更新文档 5 分钟搞定。

**经验**：
> 微调是最后的选择，不是第一选择。先问自己：Prompt 能解决吗？RAG 能解决吗？都不行再考虑微调。

**事故 2：RAG 检索质量差导致答非所问**
> 用 RAG 做知识问答，用户问"如何退货"，检索到的都是"如何购买"的文档，因为 Embedding 模型把"退货"和"购买"映射到了相似的向量空间。

**经验**：
> RAG 的核心是检索质量。要用 Hybrid Search（向量+BM25），加 Rerank 模型，还要人工检查 Top-K 结果是否相关。

**事故 3：微调后模型忘记了通用能力**
> 在医疗数据上微调后，模型医学问题答得很好，但连简单的数学题都不会了。这叫"灾难性遗忘"。

**经验**：
> 微调时要混入通用数据，比例 1:1 或 2:1（专业:通用）。或者用 LoRA 这种参数高效方法，只改部分参数，保留原有能力。

---

**导师寄语**：
> 这道题是面试官最爱考的，因为它考察你的工程思维。记住：技术选型没有"最好"，只有"最合适"。能用 Prompt 解决的，不要用 RAG；能用 RAG 解决的，不要微调。微调是最后的大杀器，不是日常工具。

**下一步**：Week 6 Day 2 — 数据工程（数据清洗/去重/质量评估）⭐⭐⭐⭐
