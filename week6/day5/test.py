
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel


# 1. 加载tokenizer
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct", trust_remote_code = True)
# 2. 加载模型（4bit）
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct", 
    trust_remote_code = True,
    quantization_config=bnb_config,
    device_map="auto",
)
model.config.use_cache = False
# 3. 配置LoRA
# 4. 处理数据（含labels masking）
# 5. 训练
# 6. 保存


# 1. 加载tokenizer
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token

# 2. 加载模型（4bit）
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
)
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True
)

# 3. 配置LoRA
lora_config = LoraConfig(
    task_type="CAUSAL_LM",
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
)
model = get_peft_model(model, lora_config)

# 4. 处理数据（含labels masking）
def tokenize(example, tokenizer):
    instruction = example.get("instruction", "")
    output = example.get("output", "")
    input_text = f"<|im_start|>user\n{instruction}<|im_end|>\n<|im_start|>assistant\n"
    full_text = input_text + output + "<|im_end|>"
    full = tokenizer(full_text, truncation=True, max_length=512, padding=False)
    input_only = tokenizer(input_text, truncation=True, max_length=512, padding=False)
    input_len = len(input_only["input_ids"])
    labels = [-100] * input_len + full["input_ids"][input_len:]
    full["labels"] = labels
    return full

# 5. 训练
trainer = Trainer(
    model=model,
    args=TrainingArguments(
        output_dir="qlora_output",
        num_train_epochs=10,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=5,
        save_steps=50,
        save_total_limit=2,
        remove_unused_columns=False,
        report_to="none",
        gradient_checkpointing=True,
        optim="paged_adamw_32bit",
    ),
    train_dataset=tokenized,
    data_collator=DataCollatorForSeq2Seq(tokenizer, padding=True),
)
trainer.train()

# 6. 保存
model.save_pretrained("qlora_output")
tokenizer.save_pretrained("qlora_output")