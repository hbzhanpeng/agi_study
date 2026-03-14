# Week 6 Day 2 学习笔记：数据工程（数据清洗/去重/质量评估）

> **学习日期**：2026-03-14  
> **面试权重**：★★★★  
> **核心价值**：微调前的数据工程是决定模型效果的关键，垃圾数据进 = 垃圾模型出

---

## 🎯 今日核心要点

### 为什么数据工程如此重要？

**业务痛点**：
- 你爬了 10 万条数据准备微调，但如果 30% 是重复的、15% 有乱码、10% 格式不统一，模型效果会暴跌
- **真实事故**：某公司用脏数据微调客服模型，结果模型输出带 HTML 标签、随机 URL、重复回答

**不做数据工程的后果**：
- 模型学到错误模式（输出乱码、格式混乱）
- 训练不收敛或过拟合
- 浪费昂贵的 GPU 时间和人力成本

---

## 📖 知识点 1：数据去噪 (Noise Removal)

### 核心原理

**前端类比**：
- 数据去噪 ≈ 前端的 `DOMPurify`（清理 XSS 攻击脚本）
- 就像你要把用户输入的 `<script>` 标签清理掉一样

### 常见噪声类型

| 噪声类型 | 示例 | 清理方法 | 正则表达式 |
|---------|------|---------|-----------|
| HTML 标签 | `<p>你好</p>` | 正则 / BeautifulSoup | `r'<[^>]+>'` |
| URL | `https://example.com` | 正则匹配 | `r'http[s]?://\S+'` |
| 多余空格 | `你好    世界` | 正则替换 | `r'\s+'` |
| 特殊字符 | 控制字符 `\x00` | 正则过滤 | `r'[\x00-\x1f\x7f-\x9f]'` |

### 核心代码

```python
import re

def remove_noise(text: str) -> str:
    # 1. 移除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 2. 移除 URL
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # 3. 移除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
```

### 面试考点

**常见问法**：
- "如何清理 HTML 标签？正则够用吗？"
- "URL 清理时要注意什么边界情况？"

**标准回答**：
> "简单场景用正则 `<[^>]+>`，复杂嵌套 HTML 用 BeautifulSoup。URL 清理要考虑 http/https、带参数的 URL、中文域名等边界情况。清理后要抽样检查，避免误删有用内容。"

### 避坑指南

- ❌ 正则写得太宽泛，把正常内容也删了（如 `<3` 被当成 HTML 标签）
- ❌ 只删标签不删属性，留下 `class="xxx"` 这种残留
- ❌ 清理过度，把代码中的特殊字符也删了

---

## 📖 知识点 2：数据去重 (Deduplication)

### 核心原理

**前端类比**：
- 数据去重 ≈ 前端的 `Array.from(new Set(arr))`
- 但文本去重更复杂，因为有"近似重复"的问题

### 两种去重策略

| 策略 | 原理 | 时间复杂度 | 适用场景 |
|------|------|-----------|---------|
| **精确去重** | MD5/SHA256 哈希比对 | O(n) | 完全相同的文本 |
| **模糊去重** | Jaccard 相似度 / Embedding | O(n²) | 语义相似的文本 |

### 核心代码

```python
import hashlib

class Deduplicator:
    def __init__(self):
        self.seen_hashes = set()
    
    def exact_dedup(self, text: str) -> bool:
        """精确去重：基于 MD5 哈希"""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        if text_hash in self.seen_hashes:
            return True  # 重复
        
        self.seen_hashes.add(text_hash)
        return False  # 不重复
    
    def fuzzy_dedup(self, text1: str, text2: str, threshold: float = 0.85) -> bool:
        """模糊去重：基于 Jaccard 相似度"""
        set1 = set(text1)
        set2 = set(text2)
        
        similarity = len(set1 & set2) / len(set1 | set2)
        return similarity >= threshold
```

### Jaccard 相似度原理

**公式**：
```
Jaccard(A, B) = |A ∩ B| / |A ∪ B|
```

**示例**：
```python
text1 = "产品很好用"
text2 = "产品很好用！"

set1 = {'产', '品', '很', '好', '用'}
set2 = {'产', '品', '很', '好', '用', '！'}

交集 = {'产', '品', '很', '好', '用'}  # 5 个
并集 = {'产', '品', '很', '好', '用', '！'}  # 6 个

相似度 = 5 / 6 = 0.83
```

### 完整去重流水线

```python
def dedup_pipeline(texts: List[str], threshold: float = 0.85):
    # 第一步：精确去重（快速过滤完全相同的）
    seen_hashes = set()
    after_exact = []
    for text in texts:
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash not in seen_hashes:
            seen_hashes.add(text_hash)
            after_exact.append(text)
    
    # 第二步：模糊去重（处理近似重复）
    final_result = []
    for text in after_exact:
        is_duplicate = False
        for kept_text in final_result:
            if jaccard_similarity(text, kept_text) >= threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            final_result.append(text)
    
    return final_result
```

### 面试考点

**常见问法**：
- "如何判断两条文本是重复的？"
- "精确去重和模糊去重的区别？"
- "10 万条数据去重，怎么优化性能？"

**标准回答**：
> "我会用两阶段去重：先用 MD5 哈希做精确去重（O(n)），快速过滤完全相同的。再用 Jaccard 相似度做模糊去重（O(n²)），阈值设为 0.85。如果数据量大（百万级），可以用 MinHash 或 LSH（局部敏感哈希）优化到 O(n)。"

### 避坑指南

- ❌ 只做精确去重，忽略标点/空格差异导致的"假不重复"
- ❌ 模糊去重阈值设置不当（太低误删，太高漏删）
- ❌ 大规模数据用 O(n²) 的两两比对，性能爆炸
- ✅ 先做精确去重，再做模糊去重（减少比对次数）

---

## 📖 知识点 3：数据质量评估 + 指令数据集格式

### 数据质量三大维度

| 维度 | 评估指标 | 检查方法 | 质量阈值（经验值） |
|------|---------|---------|------------------|
| **完整性** | 空值率、缺失字段 | 统计空文本、None 值 | 空值率 < 5% |
| **一致性** | 格式统一性、长度分布 | 检查格式、统计长度 | 标准差不要太大 |
| **准确性** | 标注正确率、语义合理性 | 抽样人工检查 | 错误率 < 10% |

### 核心代码

```python
class DataQualityChecker:
    def check_completeness(self, texts: List[str]) -> Dict:
        """检查完整性：空值率"""
        total = len(texts)
        empty_count = sum(1 for text in texts if not text or text.strip() == "")
        
        return {
            "total": total,
            "empty_count": empty_count,
            "empty_rate": empty_count / total if total > 0 else 0
        }
    
    def check_consistency(self, texts: List[str]) -> Dict:
        """检查一致性：长度分布"""
        lengths = [len(text) for text in texts if text]
        
        return {
            "min_length": min(lengths),
            "max_length": max(lengths),
            "avg_length": sum(lengths) / len(lengths)
        }
```

### 指令数据集两大格式

#### 1. Alpaca 格式（单轮指令）

**适用场景**：翻译、摘要、分类、问答等单轮任务

**格式结构**：
```json
{
  "instruction": "将下面的文本翻译成英文",
  "input": "你好，世界",
  "output": "Hello, World"
}
```

**字段说明**：
- `instruction`：任务指令（告诉模型要做什么）
- `input`：输入内容（可以为空）
- `output`：期望输出

#### 2. ShareGPT 格式（多轮对话）

**适用场景**：客服对话、助手对话、多轮问答

**格式结构**：
```json
{
  "conversations": [
    {"from": "human", "value": "你好"},
    {"from": "gpt", "value": "你好！有什么可以帮助你的吗？"},
    {"from": "human", "value": "介绍一下 Python"},
    {"from": "gpt", "value": "Python 是一种高级编程语言..."}
  ]
}
```

**字段说明**：
- `conversations`：对话列表
- `from`：角色（`human` 或 `gpt`）
- `value`：对话内容

### 格式转换代码

```python
def convert_to_alpaca(instruction: str, input_text: str, output: str) -> Dict:
    """转换为 Alpaca 格式"""
    return {
        "instruction": instruction,
        "input": input_text,
        "output": output
    }

def convert_to_sharegpt(conversations: List[tuple]) -> Dict:
    """转换为 ShareGPT 格式"""
    return {
        "conversations": [
            {"from": role, "value": content}
            for role, content in conversations
        ]
    }
```

### 面试考点

**常见问法**：
- "如何评估数据质量？用什么指标？"
- "Alpaca 和 ShareGPT 格式有什么区别？"
- "数据质量不好怎么办？"

**标准回答**：
> "我会从三个维度评估：完整性（空值率 < 5%）、一致性（长度分布合理）、准确性（抽样 100 条人工检查，错误率 < 10%）。格式方面，单轮任务用 Alpaca，多轮对话用 ShareGPT。质量不达标会重新清洗、人工标注或数据增强。"

### 避坑指南

- ❌ 不检查数据质量就直接微调
- ❌ 格式不统一（有的 Alpaca，有的 ShareGPT）
- ❌ 忽略长度分布（极短或极长的样本影响训练）
- ✅ 微调前必须做质量评估报告
- ✅ 格式转换后要验证（随机抽查 10 条）

---

## 🎯 完整数据工程流水线

```
原始数据
    ↓
【1. 数据去噪】
    - 移除 HTML 标签
    - 移除 URL
    - 移除多余空格
    ↓
【2. 格式统一】
    - 统一标点符号
    - 统一编码
    ↓
【3. 数据去重】
    - 精确去重（哈希）
    - 模糊去重（Jaccard）
    ↓
【4. 质量评估】
    - 完整性检查
    - 一致性检查
    - 准确性抽样
    ↓
【5. 格式转换】
    - Alpaca（单轮）
    - ShareGPT（多轮）
    ↓
高质量训练数据
```

---

## 💼 面试真题演练

### 题目 1：数据清洗流程

**面试官**："你是怎么做数据清洗的？具体流程是什么？"

**标准回答**：
> "我的数据清洗流程分四步：
> 1. **去噪**：用正则表达式移除 HTML 标签（`<[^>]+>`）、URL（`http[s]?://\S+`）、多余空格
> 2. **格式统一**：统一标点符号（中文标点 → 英文标点）、编码（UTF-8）
> 3. **去重**：先用 MD5 哈希做精确去重（O(n)），再用 Jaccard 相似度做模糊去重（阈值 0.85）
> 4. **质量验证**：抽样检查 100 条，统计空值率、长度分布，确保质量达标
> 
> 清洗后会生成质量报告，记录去重率、去噪率等指标。"

### 题目 2：去重策略选择

**面试官**："如何判断两条文本是重复的？完全匹配还是语义相似？"

**标准回答**：
> "我会用两阶段去重：
> 1. **精确去重**：用 MD5 哈希，时间复杂度 O(n)，快速过滤完全相同的文本
> 2. **模糊去重**：用 Jaccard 相似度，阈值设为 0.85。计算公式是 `|A ∩ B| / |A ∪ B|`，即字符集合的交集除以并集
> 
> 如果数据量大（百万级），会用 MinHash 或 LSH（局部敏感哈希）优化到 O(n)。
> 
> 阈值选择：0.85 是经验值，可以根据业务调整。太低会误删，太高会漏删。"

### 题目 3：数据质量评估

**面试官**："数据清洗后如何验证质量？"

**标准回答**：
> "我会从三个维度评估：
> 1. **完整性**：统计空值率，要求 < 5%
> 2. **一致性**：统计长度分布（最小/最大/平均），检查是否有极端值
> 3. **准确性**：随机抽样 100 条人工检查，错误率要求 < 10%
> 
> 评估后会生成质量报告，包含：
> - 原始数据量 vs 清洗后数据量
> - 去重率、去噪率
> - 长度分布统计
> - 抽样检查结果
> 
> 质量不达标会重新清洗或人工标注。"

### 题目 4：Alpaca vs ShareGPT

**面试官**："Alpaca 和 ShareGPT 格式有什么区别？什么时候用哪个？"

**标准回答**：
> "两者的核心区别是**任务类型**：
> 
> **Alpaca 格式**：
> - 结构：`{"instruction": "...", "input": "...", "output": "..."}`
> - 适用：单轮指令任务（翻译、摘要、分类、问答）
> - 特点：明确的输入输出，任务导向
> 
> **ShareGPT 格式**：
> - 结构：`{"conversations": [{"from": "human/gpt", "value": "..."}]}`
> - 适用：多轮对话（客服、助手、聊天机器人）
> - 特点：保留对话上下文，支持多轮交互
> 
> **选型依据**：
> - 如果是单次任务（如翻译）→ Alpaca
> - 如果需要多轮交互（如客服）→ ShareGPT
> - 如果两者都有，可以分别构建数据集，或统一转换为 ShareGPT（更通用）"

---

## 🔥 工程经验总结

### 真实踩坑经历

1. **坑 1：只做精确去重，忽略近似重复**
   - 问题：`"产品很好用！"` 和 `"产品很好用!!!"` 被当成不同文本
   - 解决：加入模糊去重，Jaccard 阈值 0.85

2. **坑 2：清洗过度，把有用内容也删了**
   - 问题：代码数据集中的 `<template>` 标签被当成 HTML 删除
   - 解决：根据数据类型调整清洗规则，代码数据不清理特殊字符

3. **坑 3：不验证清洗效果，直接微调**
   - 问题：清洗后还有 20% 的乱码数据，模型效果很差
   - 解决：清洗后必须抽样检查 100 条，生成质量报告

### 最佳实践

1. **清洗前后都要抽样检查**（至少 100 条）
2. **记录清洗统计**（去重率、去噪率），写入日志
3. **保留原始数据备份**，清洗脚本要可复现
4. **质量阈值**：空值率 < 5%，人工抽样错误率 < 10%
5. **格式转换后验证**：随机抽查 10 条，确保结构正确

---

## 📚 延伸阅读

### 进阶技术

1. **MinHash**：用于大规模文本去重，时间复杂度 O(n)
2. **LSH（局部敏感哈希）**：快速找到相似文本，不需要两两比对
3. **Embedding 相似度**：用向量余弦相似度，比 Jaccard 更准确（但更慢）
4. **数据增强**：回译、同义词替换、句式变换

### 相关论文

- 《Data Quality for Machine Learning》
- 《Deduplication of Training Data Makes Language Models Better》

---

## ✅ 今日学习检查清单

- [x] 理解数据去噪的原理和方法
- [x] 掌握精确去重和模糊去重的区别
- [x] 学会用 Jaccard 相似度计算文本相似度
- [x] 理解数据质量三大维度（完整性、一致性、准确性）
- [x] 掌握 Alpaca 和 ShareGPT 两种格式的区别和应用场景
- [x] 完成 3 个实战练习（去噪、去重、质量评估）

---

## 🎯 明日预告

**第 6 周 Day 3：参数高效微调 PEFT（LoRA/QLoRA 原理）**

**预习内容**：
- 什么是参数高效微调？为什么需要它？
- LoRA 的核心思想是什么？
- 秩分解（Rank Decomposition）是什么？

**明日重点**：
- LoRA 原理（低秩分解）
- QLoRA 优化（量化 + LoRA）
- 超参数选择（秩 r、alpha、dropout）

晚安，明天见！💪
