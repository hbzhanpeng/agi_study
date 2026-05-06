import os
import sys
import io
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Windows 控制台 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ===== 1. 配置 =====
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
LORA_DIR = os.path.join(_BASE_DIR, "qlora_output")
MERGED_DIR = os.path.join(_BASE_DIR, "merged_model")

def main():
    print(f"=== 1. 加载 Base Model ({BASE_MODEL}) ===")
    # 注意：合并模型时，不可以开启 4bit 量化 (load_in_4bit=True) 
    # 必须以 float16 原精度加载，否则无法正确合并计算
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="cpu",  # 内存够的话建议用 CPU 合并，防止爆显存
        trust_remote_code=True
    )
    
    print(f"=== 2. 加载 Tokenizer ===")
    tokenizer = AutoTokenizer.from_pretrained(
        LORA_DIR, # 优先使用训练保存的 tokenizer，防止新增 special token 丢失
        trust_remote_code=True
    )

    print(f"=== 3. 挂载 LoRA 权重 ({LORA_DIR}) ===")
    # 这一步只是相当于把两套权重放进了内存，用类似"加法器"连接
    peft_model = PeftModel.from_pretrained(base_model, LORA_DIR)

    print(f"=== 4. 融合权重并卸载 LoRA 外壳 (Merge and Unload) ===")
    # 核心：将 W = W_base + A * B 算出来，固化到一个新的 W_merged 里
    # 返回的就是一个完整的、没有任何 PEFT 痕迹的普通 Hugging Face 模型
    merged_model = peft_model.merge_and_unload()

    print(f"=== 5. 保存完整新模型到：{MERGED_DIR} ===")
    os.makedirs(MERGED_DIR, exist_ok=True)
    merged_model.save_pretrained(MERGED_DIR)
    tokenizer.save_pretrained(MERGED_DIR)
    
    print("🎉 合并完成！现在你可以像加载官方模型一样，直接加载这个合并后的文件夹了！")

if __name__ == "__main__":
    main()
