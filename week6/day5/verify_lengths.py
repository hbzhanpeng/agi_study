
import torch
from transformers import AutoTokenizer
import json
import os

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
MAX_LENGTH = 512

def test_lengths():
    print(f"Loading tokenizer: {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    
    # 模拟数据
    instruction = "results 没有传给 LLM"
    output = "【问题】results 没有传给 LLM\n【原因】写的时候只拿了检索的结果，并没有让llm 从检索的结果中去回答问题。\n【解决】讲检索的结果作为content 传入prompt，让llm基于检索的结果进行回答问题。检索部分还可以优化，先用llm 回答问题，然后用llm 回答的问题去资源库中检索，这样得到正确的概率应该会更高"
    
    input_text = f"<|im_start|>user\n{instruction}<|im_end|>\n<|im_start|>assistant\n"
    full_text = input_text + output + "<|im_end|>"
    
    full = tokenizer(full_text, truncation=True, max_length=MAX_LENGTH, padding=False)
    input_only = tokenizer(input_text, truncation=True, max_length=MAX_LENGTH, padding=False)
    
    input_len = len(input_only["input_ids"])
    total_len = len(full["input_ids"])
    output_len = total_len - input_len
    
    print(f"\n--- 验证结果 ---")
    print(f"问题 (Instruction): {instruction}")
    print(f"Prompt 长度 (input_len): {input_len}")
    print(f"回答 长度 (output_len): {output_len}")
    print(f"总长度 (total_len): {total_len}")
    
    print("\n【结论】")
    if output_len > input_len:
        print("因为你的‘回答’包含了完整的排查笔记，而‘问题’只有一句话，所以 output_len > input_len 是符合预期的。")
        print("教程里说应更小，是因为教程假设背景知识（Context）已经放在了 Prompt 里。")

if __name__ == "__main__":
    test_lengths()
