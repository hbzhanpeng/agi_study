# train.py - QLoRA微调训练脚本
import json
import os
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, TaskType

import sys
import io

# Windows 控制台 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ===== 1. 配置 =====
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"  # 升级到 7B，显存占用约 5.5GB (4-bit)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(_BASE_DIR, "train.json")
OUTPUT_DIR = os.path.join(_BASE_DIR, "qlora_output")
MAX_LENGTH = 512

# ===== 2. 加载数据 =====
def load_data(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# ===== 3. 格式化为对话格式 =====


# ===== 4. Tokenize =====
def tokenize(example, tokenizer):
    
    # 分离input和output部分
    instruction = example.get("instruction", "")
    output = example.get("output", "")
    
    # 只有input部分
    input_text = f"<|im_start|>user\n{instruction}<|im_end|>\n<|im_start|>assistant\n"
    full_text = input_text + output + "<|im_end|>"

    # # 只有input部分，用来算长度
    # input_text = tokenizer.apply_chat_template(
    #     [{"role": "user", "content": instruction}],
    #     tokenize=False,
    #     add_generation_prompt=True
    # )

    # full_text = tokenizer.apply_chat_template(
    #     [{"role": "user", "content": instruction},
    #     {"role": "assistant", "content": output}],
    #     tokenize=False,
    #     add_generation_prompt=False
    # )
    
    # tokenize完整文本
    full = tokenizer(full_text, truncation=True, max_length=MAX_LENGTH, padding=False)
    
    # tokenize input部分，得到长度
    input_only = tokenizer(input_text, truncation=True, max_length=MAX_LENGTH, padding=False)
    input_len = len(input_only["input_ids"])
    
    # labels：input部分设为-100（不计算loss），只学output部分
    labels = [-100] * input_len + full["input_ids"][input_len:]
    
    full["labels"] = labels
    print(f"input_len: {input_len}, total_len: {len(full['input_ids'])}, output_len: {len(full['input_ids'])-input_len}")

    return full

# ===== 5. 主流程 =====
def main():
    print("=== Step 1: 加载tokenizer ===")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True
    )
    tokenizer.pad_token = tokenizer.eos_token

    print("=== Step 2: 加载模型（4bit量化）===")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    model.config.use_cache = False

    print("=== Step 3: 配置LoRA ===")
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=8,                          # rank，小数据集用8够了
        lora_alpha=16,                # 通常是r的2倍
        target_modules=["q_proj", "v_proj"],  # 只训练注意力层
        lora_dropout=0.05,
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()  # 看看训练了多少参数

    print("=== Step 4: 准备数据集 ===")
    raw_data = load_data(DATA_PATH)
    dataset = Dataset.from_list(raw_data)
    tokenized = dataset.map(
        lambda x: tokenize(x, tokenizer),
        remove_columns=dataset.column_names  # 删除所有原始列
    )
    print(f"训练样本数: {len(tokenized)}")

    print("=== Step 5: 训练 ===")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=10,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,  # 等效batch_size=4
        learning_rate=2e-4,
        fp16=True,
        logging_steps=5,
        save_steps=50,
        save_total_limit=2,
        remove_unused_columns=False,
        report_to="none",               # 不用wandb
        gradient_checkpointing=True,    # 关键：用计算换显存
        optim="paged_adamw_32bit",      # 关键：将优化器状态分页到内存，防止OOM
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=DataCollatorForSeq2Seq(tokenizer, padding=True),
    )
    trainer.train()

    print("=== Step 6: 保存LoRA权重 ===")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"训练完成！权重保存在 {OUTPUT_DIR}")

if __name__ == "__main__":
    main()