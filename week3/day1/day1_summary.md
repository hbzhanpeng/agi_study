# 第 3 周 Day 1 学习总结：OpenAI API 全参数详解

> **核心目标：掌握 LLM API 核心参数的原理和使用场景。**

---

## 1. temperature 参数

### 原理
控制输出概率分布的"尖锐程度"：`softmax(logits / temperature)`

```
temperature 低（0~0.3）→ 分布尖锐 → 输出确定
temperature 高（0.7~1.5）→ 分布平坦 → 输出随机
```

### 场景选择

| 场景 | temperature | 原因 |
|------|------------|------|
| 代码生成 | 0 ~ 0.2 | 要精确 |
| 客服问答 | 0.3 ~ 0.5 | 准确但自然 |
| 创意写作 | 0.7 ~ 1.0 | 需要多样性 |
| 医疗问诊 | 0 ~ 0.2 | 不能瞎编，事关安全 |

---

## 2. top_p 参数（Nucleus Sampling）

### 原理
只从概率累计达到 p 的候选词中采样

```
top_p = 0.1 → 只从最高概率的前 10% 词中选
top_p = 0.9 → 从累计 90% 概率的词中选
```

### 关键规则
- **不建议同时调 temperature 和 top_p**，只调其中一个
- OpenAI 官方也这样建议

---

## 3. 其他关键参数

| 参数 | 作用 | 典型用法 |
|------|------|---------|
| `max_tokens` | 控制输出最大长度 | 控成本、防话痨 |
| `stop` | 遇到特定字符停止 | `["\n\n"]` 函数结束停、`["}"]` JSON 结束停 |
| `frequency_penalty` | 惩罚重复用词 | 0.5~1.0 减少车轱辘话 |
| `presence_penalty` | 鼓励新话题 | 0.5~1.0 创意场景 |
| `logprobs` | 返回 token 概率 | 置信度评估、调试 |

### 注意事项
- `max_tokens` 是**输出**上限，不含输入
- 总 token = 输入 + 输出 ≤ 模型上下文窗口

---

## 4. 面试考点

### 必答题：temperature vs top_p
- temperature 控制分布尖锐度，top_p 控制采样范围
- 不建议同时调，二选一

### 场景题：AI 代码助手参数
```python
# 最佳配置
temperature=0        # greedy decoding，确定性输出
max_tokens=2000      # 代码可能很长
stop=["\n\n"]        # 函数结束自然分隔
frequency_penalty=0  # 代码允许重复模式（如循环）
```

---

## 5. 避坑指南

1. **temperature=0** 不是"零随机"，是 greedy decoding（取概率最高的词）
2. **不要同时调 temperature 和 top_p**，效果不可控
3. **max_tokens 控成本**：线上必须设置，不设可能烧钱
4. **安全场景必须低 temperature** + 人工审核兜底

---

## 6. 下一步学习

**明天内容**：Prompt Engineering 系统化（Zero/Few-shot, CoT, ToT, ReAct）

**预习问题**：
1. 什么是 Chain of Thought (CoT)？
2. Zero-Shot CoT 和 Few-Shot CoT 有什么区别？
3. 什么场景适合用 CoT？
