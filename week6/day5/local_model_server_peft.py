import os
import torch
import json
from threading import Thread
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer, BitsAndBytesConfig
from peft import PeftModel

app = FastAPI()

# ===== 路径配置 =====
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 1. 指向原始的、没动过的基座模型
BASE_MODEL_PATH = "Qwen/Qwen2.5-7B-Instruct" 
# 2. 指向你微调完产生的那个文件夹（里面有 adapter_config.json）
LORA_PATH = os.path.join(_BASE_DIR, "qlora_output")

print(f"正在以 [外挂模式] 加载模型...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH, trust_remote_code=True)

# 关键：7B 模型必须开启 4bit 量化才能在 8GB 显存运行
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

# 先加载基座
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_PATH,
    quantization_config=bnb_config,
    device_map={"": 0},
    torch_dtype=torch.float16,
    trust_remote_code=True
)

# 再把 LoRA 挂上去
# model = base_model 
model = PeftModel.from_pretrained(base_model, LORA_PATH)
print("✅ LoRA 外挂加载完毕！服务启动在 http://localhost:8001")

class ChatRequest(BaseModel):
    messages: list
    max_tokens: int = 500
    stream: bool = False
    model: str = ""
    temperature: float = 0.7
    tools: list = None

@app.post("/v1/chat/completions")
def chat_completions(req: ChatRequest):
    # 使用官方推荐的 apply_chat_template 格式化完整历史记录
    prompt = tokenizer.apply_chat_template(
        req.messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    if req.stream:
        # 处理流式请求
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = dict(
            **inputs,
            max_new_tokens=req.max_tokens,
            pad_token_id=tokenizer.eos_token_id,
            streamer=streamer
        )
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()

        def generate_sse():
            for text in streamer:
                # 伪装 SSE Chunk 格式
                chunk = {"choices": [{"delta": {"content": text}}]}
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            
        return StreamingResponse(generate_sse(), media_type="text/event-stream")
    else:
        # 处理阻塞请求
        with torch.no_grad():
            outputs = model.generate(
                **inputs, 
                max_new_tokens=req.max_tokens, 
                pad_token_id=tokenizer.eos_token_id
            )
        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        answer = tokenizer.decode(new_tokens, skip_special_tokens=True)
        return {"choices": [{"message": {"role": "assistant", "content": answer}}]}
