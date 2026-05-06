import os
import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM

app = FastAPI()

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 指向我们刚刚合并完的完整模型文件夹
MODEL_DIR = os.path.join(_BASE_DIR, "merged_model")

print("正在加载本地微调模型，请稍候...")
# 因为是推理，这里可以用 4bit 或者 8bit 量化加载来省显存，也可以全精度
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR, 
    torch_dtype=torch.float16, 
    device_map="auto",
    trust_remote_code=True
)
print("✅ 模型加载完毕，服务启动在 http://localhost:8001")

import json
from threading import Thread
from fastapi.responses import StreamingResponse
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer

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
    # 这是 0.5B 小模型能理解多轮对话的关键
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
