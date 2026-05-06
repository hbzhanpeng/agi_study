# QLoRA & RAG 系统学习复习手册
 
> 重点概念 · 核心代码 · 面试要点
 
---
 
## 一、QLoRA 微调训练流程
 
### 1.1 训练的本质
 
**训练 = 调整模型参数，让模型输出和期望输出越来越接近。**
 
- 衡量"接近程度"用 **loss**，loss 越小越好
- 调整参数用 **梯度下降**，每次往 loss 减小的方向更新
 
```
准备数据（input + 期望output）
    ↓
模型看input，生成预测output
    ↓
计算预测output和期望output的差距（loss）
    ↓
反向传播，更新参数
    ↓
重复，直到loss足够小
```
 
### 1.2 为什么用 QLoRA 而不是全量微调
 
| 方案 | 显存需求 | 说明 |
|------|----------|------|
| 全量微调 float32 | 28 GB | 7B × 4字节 |
| 全量微调 float16 | 14 GB | 7B × 2字节 |
| int8 量化 | 7 GB | 7B × 1字节 |
| **QLoRA（4bit）** | **3.5 GB** | 7B × 0.5字节，8GB显存装得下 |
 
**QLoRA = 4bit量化 + LoRA**，显存和效果的最佳平衡。
 
---
 
## 二、4bit 量化（BitsAndBytesConfig）
 
### 2.1 原理
 
把每个参数从 float16（2字节）压缩到 4bit（0.5字节），显存缩小4倍。
 
- **存储用4bit**：省显存
- **计算时还原成fp16**：保精度
- **NF4格式**：专为神经网络权重的正态分布设计，比普通int4精度更高
 
> int4 vs NF4：int4把0-15均匀分16格；NF4把16格集中在数据密集区域，稀疏区域少分。
 
### 2.2 代码解析
 
```python
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,              # 用4bit加载，7B从14GB压到3.5GB
    bnb_4bit_use_double_quant=True, # 二次量化，对量化参数本身再压一次，额外省0.4GB
    bnb_4bit_quant_type="nf4",      # NF4格式，专为正态分布权重设计，精度损失最小
    bnb_4bit_compute_dtype=torch.float16,  # 计算时临时还原成fp16，算完再压回去
)
 
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config, # 传入量化配置
    device_map="auto",              # 自动分配到GPU，显存不够的放CPU
    trust_remote_code=True          # Qwen有自定义代码，允许执行
)
model.config.use_cache = False      # 训练时不需要KV Cache，关掉省显存
```
 
---
 
## 三、LoRA 配置（LoraConfig）
 
### 3.1 核心思想
 
保留原始权重W不变，新增两个小矩阵A和B，只训练A和B。
 
```
原来：y = Wx         （W是7B参数，冻结不动）
LoRA：y = Wx + ABx   （只训练A和B，参数量极少）
 
W的形状：4096 × 4096 = 1677万参数
A的形状：4096 × 8   = 3万参数   ← r=8
B的形状：8 × 4096   = 3万参数
```
 
### 3.2 参数逐行解析
 
```python
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,        # GPT类模型（因果语言模型）
    r=8,                                  # 秩，AB矩阵中间维度，越小参数越少
    lora_alpha=16,                        # 缩放系数，实际公式是(alpha/r)×ABx = 2×ABx
    target_modules=["q_proj", "v_proj"], # 在Attention的Q和V矩阵上加LoRA
    lora_dropout=0.05,                   # 随机丢弃5%的LoRA参数，防止过拟合
    bias="none",                          # 不训练bias，只训练AB矩阵
)
model = get_peft_model(model, lora_config)  # 冻结原始权重，只有AB可训练
model.print_trainable_parameters()          # 打印可训练参数量（约0.1%）
```
 
### 3.3 为什么选 q_proj 和 v_proj
 
- **Q** 影响注意力分布（关注哪里）
- **V** 影响输出内容（输出什么）
- LoRA原论文实验结论：这两个性价比最高，K相对固定不需要微调
 
---
 
## 四、Labels Masking（核心难点）
 
### 4.1 为什么要 Masking
 
模型是**自回归**的，每个位置预测下一个token。
 
❌ **不Masking**：问题部分也计算loss，模型会学着复述问题
```
模型努力学：看到 <|im_start|>user，预测下一个词是"硬"
           看到 "硬"，预测下一个词是"切" ...
结果：学会了复述问题，不会回答
```
 
✅ **Masking后**：只有输出部分计算loss，模型只学如何回答
```
问题部分 labels = -100  → PyTorch CrossEntropyLoss 遇到-100自动跳过
答案部分 labels = 真实token id → 计算loss，模型学这里
```
 
### 4.2 代码实现
 
```python
def tokenize(example, tokenizer):
    instruction = example.get("instruction", "")
    output = example.get("output", "")
 
    # 问题部分
    input_text = f"<|im_start|>user\n{instruction}<|im_end|>\n<|im_start|>assistant\n"
    # 完整文本（问题 + 答案）
    full_text = input_text + output + "<|im_end|>"
 
    # tokenize完整文本
    full = tokenizer(full_text, truncation=True, max_length=512, padding=False)
    # tokenize问题部分，只是为了得到长度
    input_only = tokenizer(input_text, truncation=True, max_length=512, padding=False)
    input_len = len(input_only["input_ids"])
 
    # 关键：问题部分设-100，只让模型学输出
    labels = [-100] * input_len + full["input_ids"][input_len:]
    full["labels"] = labels
    return full
```
 
### 4.3 -100 的含义
 
- `-100` 是 PyTorch 的约定，和数字100没有任何关系
- CrossEntropyLoss 遇到 `-100` 直接跳过，不计算该位置的loss
- 如果问题部分token数超过max_length，output会被截断，labels全为-100，这条数据白训练
 
---
 
## 五、训练参数（TrainingArguments）
 
```python
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=10,                # 50条数据需要10轮才能充分学习
    per_device_train_batch_size=1,      # 每次喂1条，显存紧张必须设1
    gradient_accumulation_steps=4,      # 积累4步再更新，等效batch_size=4
    learning_rate=2e-4,                 # LoRA微调推荐值
    fp16=True,                          # 半精度训练，省显存加速
    logging_steps=5,                    # 每5步打印一次loss
    save_steps=50,                      # 每50步保存一次checkpoint
    save_total_limit=2,                 # 最多保留2个checkpoint，防硬盘爆
    remove_unused_columns=False,        # 关掉自动删列，防止误删labels
    report_to="none",                   # 不上传wandb
    gradient_checkpointing=True,        # 用计算换显存，省约30%，训练慢20%
    optim="paged_adamw_32bit",          # 优化器状态分页到CPU内存，防OOM关键参数
)
```
 
**gradient_accumulation 理解**：
```
batch_size=1，积累4步 = 等效batch_size=4
Step1: 计算loss，不更新
Step2: 计算loss，不更新
Step3: 计算loss，不更新
Step4: 计算loss，合并梯度，更新参数
```
 
---
 
## 六、Loss 诊断与验证
 
### 6.1 Loss 参考范围
 
| Loss 范围 | 含义 | 处理 |
|-----------|------|------|
| > 2.0 | 没学到东西 | 检查labels masking是否生效 |
| 1.0 ~ 2.0 | 学了一点 | 增加epoch或数据量 |
| 0.5 ~ 1.0 | 基本学到了 | 格式和内容都不错 |
| < 0.5 | 可能过拟合 | 减少epoch，增加数据量 |
 
### 6.2 完整验证体系
 
```
训练时 → 看loss曲线是否持续下降
训练后 → inference测试格式是否正确（有无【问题】【原因】【解决】）
深度验证 → eval.py对比期望答案和实际输出的准确率
```
 
### 6.3 本次 Debug 经历（面试素材）
 
```
第一次：loss=2.9  ← labels没有masking，模型在学复述问题
第二次：loss=2.2  ← masking生效但epoch=3不够
第三次：loss<1.0  ← epoch=10，格式完全学到了
```
 
---
 
## 七、Chat Template（对话格式）
 
每个模型都有自己的对话格式，格式写错效果很差。
 
```python
# Qwen2.5 格式
<|im_start|>user
你好<|im_end|>
<|im_start|>assistant
你好！<|im_end|>
 
# LLaMA3 格式
<|begin_of_text|><|start_header_id|>user<|end_header_id|>
你好<|eot_id|><|start_header_id|>assistant<|end_header_id|>
```
 
**推荐做法**：用 `apply_chat_template` 自动生成，换模型不用改代码
 
```python
input_text = tokenizer.apply_chat_template(
    [{"role": "user", "content": instruction}],
    tokenize=False,
    add_generation_prompt=True  # 自动加上 <|im_start|>assistant\n
)
```
 
---
 
## 八、推理流程（inference.py）
 
```python
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, ...)
    model = PeftModel.from_pretrained(base_model, LORA_PATH)  # ← 必须加载LoRA权重
    model.eval()   # ← 必须，关掉dropout
    return model, tokenizer
 
def ask(question, model, tokenizer):
    text = f"<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n"
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
 
    with torch.no_grad():  # 推理不需要梯度，省显存
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0,       # 确定性输出
            do_sample=False,     # 贪婪解码，双重保险
            eos_token_id=tokenizer.eos_token_id,
        )
 
    # 只取新生成的部分，不包含输入
    new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)
```
 
**常见错误**：
 
- 忘记加载LoRA权重 → 用纯base model，格式答不出来
- 忘记 `model.eval()` → dropout仍在训练模式，输出不稳定
- 不截取 new_tokens → decode出来包含问题本身
 
---
 
## 九、面试核心话术
 
### 被问：讲一下你的微调方案
 
> 1. **为什么QLoRA**：7B模型float16需要14GB，我的显卡只有8GB，4bit量化后压到3.5GB
> 2. **为什么LoRA**：全量微调需要更新所有参数，LoRA只训练AB矩阵，可训练参数从70亿降到几万
> 3. **Labels masking**：只让模型学输出格式，input部分设-100跳过，否则模型学复述问题
> 4. **结果**：loss从2.9降到1.0以下，模型学到了【问题】【原因】【解决】的输出格式
 
### 被问：遇到什么问题怎么解决的
 
> 第一个问题：loss卡在2.9，排查发现labels没有masking，问题和答案都在计算loss，模型在学复述而不是回答。解决：把input部分labels设为-100。
>
> 第二个问题：loss降到2.2但格式还不稳定。解决：epoch从3增加到10，loss降到1.0以下，格式完全学到了。
 
### 被问：微调效果怎么验证
 
> - 格式验证：inference测试，输出有没有【问题】【原因】【解决】
> - 内容验证：对比训练集期望答案，内容意思是否相近
> - 关键结论：模型在泛化而不是死记硬背，说明真正学到了任务模式
 
---
 
## 附录：快速参考
 
### 显存估算
 
| 模型规模 | float32 | float16 | int8 | int4(QLoRA) |
|----------|---------|---------|------|-------------|
| 7B | 28 GB | 14 GB | 7 GB | **3.5 GB** |
| 1.5B | 6 GB | 3 GB | 1.5 GB | **0.75 GB** |
| 0.5B | 2 GB | 1 GB | 0.5 GB | **0.25 GB** |
 
### 常用命令
 
```bash
# 验证CUDA环境
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
 
# 训练并查看loss
python train.py 2>&1 | findstr "loss"
 
# 推理测试
python inference.py
```
 
### 文件结构
 
```
week6/day5/
├── config.py          # 统一配置
├── rag.py             # RAG核心（HyDE + 问题改写 + 多轮对话）
├── agent.py           # Agent（Function Calling + ReAct循环）
├── api.py             # FastAPI后端
├── eval.py            # 评估脚本（87.5% vs 75% 有/无HyDE对比）
├── train.py           # QLoRA训练脚本  ← 今天新增
├── inference.py       # 推理测试脚本   ← 今天新增
├── train.json         # 50条训练数据   ← 今天扩充
├── qlora_output/      # 训练好的LoRA权重
└── chroma_db/         # 向量数据库
```