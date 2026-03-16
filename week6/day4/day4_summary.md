# Week 6 Day 4 学习笔记：全参微调流程（Trainer/监控/分布式）

> **学习日期**：2026-03-16  
> **面试权重**：★★★★  
> **核心价值**：掌握完整的微调工程链路，从训练到监控到分布式

---

## 📖 知识点 1：Hugging Face Trainer API

### 核心组件

```
Trainer
  ├─ Model（模型）
  ├─ TrainingArguments（训练配置）
  ├─ Dataset（数据集）
  ├─ DataCollator（数据整理器）
  └─ Callbacks（回调函数）
```

### 关键参数速查

| 参数 | 作用 | 推荐值 |
|------|------|--------|
| per_device_train_batch_size | 每 GPU batch | 4-8 |
| gradient_accumulation_steps | 梯度累积 | 4-8 |
| learning_rate | 学习率 | 全参 1e-5，LoRA 2e-4 |
| fp16 | 混合精度 | True |
| max_grad_norm | 梯度裁剪 | 1.0 |
| weight_decay | 正则化 | 0.01-0.1 |
| warmup_steps | 预热步数 | 总步数 10% |

### 有效 Batch Size 计算

```
有效 batch_size = per_device_batch_size × gradient_accumulation_steps × num_gpus
```

---

## 📖 知识点 2：训练监控与调试

### 常见问题诊断

| 症状 | 问题 | 解决方案 |
|------|------|---------|
| Loss 下降慢，梯度正常 | 学习率太小 | 增大学习率 10x |
| Loss NaN，梯度爆炸 | 梯度爆炸 | max_grad_norm=1.0 + 降低 lr |
| train_loss 降，eval_loss 升 | 过拟合 | weight_decay=0.1 + 早停 |
| Loss 震荡 | 学习率太大 | 降低学习率 |
| OOM | 显存不够 | 减小 batch_size + gradient_checkpointing |

### 监控工具

- **TensorBoard**：本地可视化，`report_to="tensorboard"`
- **WandB**：云端协作，`report_to="wandb"`

---

## 📖 知识点 3：分布式训练（DeepSpeed/FSDP）

### 三种并行策略

| 策略 | 原理 | 适用场景 |
|------|------|---------|
| 数据并行 | 每卡完整模型，处理不同数据 | 模型 < 10B |
| 模型并行 | 模型切分到多卡 | 超大模型 |
| 混合并行 | 数据 + 模型并行 | 最优方案 |

### DeepSpeed ZeRO 三阶段

| 阶段 | 分片内容 | 显存节省 |
|------|---------|---------|
| ZeRO-1 | 优化器状态 | 4x |
| ZeRO-2 | 优化器 + 梯度 | 8x |
| ZeRO-3 | 优化器 + 梯度 + 模型 | 64x+ |

### 显存计算公式

```
数据并行：模型 × 4
ZeRO-2：模型 + 模型×2/N
ZeRO-3：模型×4/N
```

### 选型决策树

```
单卡能装下？
  ├─ 是 → 数据并行（最快）
  ↓
  否
  ↓
ZeRO-2 能装下？
  ├─ 是 → DeepSpeed ZeRO-2（推荐）
  ↓
  否
  ↓
DeepSpeed ZeRO-3 + CPU offload
```

---

## 💼 面试真题

**Q：显存不够怎么办？**
> fp16 → 减小 batch_size + 增大 gradient_accumulation → gradient_checkpointing → ZeRO

**Q：Loss 为 NaN 怎么办？**
> 检查梯度范数 → 开启梯度裁剪（max_grad_norm=1.0）→ 降低学习率 → 关闭 fp16

**Q：4 张 A100 训练 65B 模型怎么做？**
> DeepSpeed ZeRO-3 + CPU offload，显存从 130GB 降到 ~70GB/卡

---

## ✅ 今日检查清单

- [x] 掌握 Trainer API 核心组件和参数
- [x] 理解梯度累积和有效 batch_size
- [x] 学会诊断常见训练问题
- [x] 掌握 DeepSpeed ZeRO 三阶段
- [x] 能根据模型大小选择分布式策略

---

## 🎯 明日预告

**第 6 周 Day 5：RLHF/DPO 对齐技术**

预习内容：
- 什么是 RLHF？为什么需要对齐？
- DPO 和 RLHF 的区别？
- 奖励模型是什么？
