# inference.py - 加载 LoRA 权重，测试微调效果
import os
import sys
import io
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# Windows 控制台 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_MODEL  = "Qwen/Qwen2.5-7B-Instruct"
LORA_DIR    = os.path.join(_BASE_DIR, "qlora_output")

# # ===== 1. 加载 tokenizer =====
# print("加载 tokenizer...")
# tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
# tokenizer.pad_token = tokenizer.eos_token

# # ===== 2. 加载 base model（4bit 量化）=====
# print("加载 base model（4bit 量化）...")
# bnb_config = BitsAndBytesConfig(
#     load_in_4bit=True,
#     bnb_4bit_use_double_quant=True,
#     bnb_4bit_quant_type="nf4",
#     bnb_4bit_compute_dtype=torch.float16,
# )
# model = AutoModelForCausalLM.from_pretrained(
#     BASE_MODEL,
#     quantization_config=bnb_config,
#     device_map="auto",
#     trust_remote_code=True
# )

# # ===== 3. 挂载 LoRA 权重 =====
# print(f"挂载 LoRA 权重：{LORA_DIR}")
# model = PeftModel.from_pretrained(model, LORA_DIR)
# model.eval()
# print("模型就绪！\n")


# def ask(question: str, max_new_tokens: int = 300) -> str:
#     """用微调后的模型回答问题"""
#     prompt = f"<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n"
#     inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
#     with torch.no_grad():
#         outputs = model.generate(
#             **inputs,
#             max_new_tokens=max_new_tokens,
#             do_sample=False,          # greedy，结果可复现
#             eos_token_id=tokenizer.eos_token_id,
#             pad_token_id=tokenizer.eos_token_id,
#             repetition_penalty=1.1,  # 增加这一行，效果更佳
#         )
#     # 只截取新生成的部分
#     new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
#     return tokenizer.decode(new_tokens, skip_special_tokens=True)


# # ===== 4. 测试题（来自 train.json 的真实坑）=====
# test_questions = [
#     "ChromaDB重复添加文档导致检索结果重复，怎么解决？",
#     "Agent工具调用后LLM忽略了工具返回结果，是什么原因？",
#     "LoRA训练loss不下降怎么办？",
#     "FastAPI接口跨域请求被浏览器拦截如何处理？",
# ]

# print("=" * 60)
# print("微调后模型效果测试")
# print("=" * 60)

# for i, q in enumerate(test_questions, 1):
#     print(f"\n【问题 {i}】{q}")
#     print("-" * 40)
#     answer = ask(q)
#     print(answer)
#     print()

# inference.py - 测试微调后的模型
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel


def load_model():
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    # 加载LoRA权重
    model = PeftModel.from_pretrained(base_model, LORA_DIR)
    model.eval()
    return model, tokenizer

def ask(question, model, tokenizer):
    text = f"<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n"
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0,
            do_sample=False,
            eos_token_id=tokenizer.eos_token_id,
        )
    # 只取新生成的部分
    new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)

if __name__ == "__main__":
    print("加载模型中...")
    model, tokenizer = load_model()
    
    # 用训练数据里的问题测试
    test_questions = [
        "硬切分片破坏语义",
        "QLoRA训练时显存OOM",
        "ChromaDB重复添加文档导致检索结果重复",
    ]
    
    for q in test_questions:
        print(f"\n问题：{q}")
        print(f"回答：{ask(q, model, tokenizer)}")
        print("-" * 50)