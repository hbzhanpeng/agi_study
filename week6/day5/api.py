from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from rag import ask, add_note
from agent import run_agent, run_agent_stream
from fastapi.responses import StreamingResponse

# 创建 FastAPI 实例 (类似前端的 const app = express())
app = FastAPI(
    title="AGI 学习助手 API",
    description="这是一个专门用来学习大模型开发的 API",
    version="1.0.0"
)

# 定义根路由 (类似 app.get('/', (req, res) => ...))
@app.get("/")
def read_root():
    return {"message": "Welcome to AGI API!", "status": "online"}


class AskRequest(BaseModel):
    question: str
    history: list = []


@app.post("/ask")
def ask_endpoint(req: AskRequest):
    """普通接口：等待完整回答后一次性返回"""
    answer = run_agent(req.question)
    return {"answer": answer}


@app.post("/ask/stream")
def ask_stream_endpoint(req: AskRequest):
    """流式接口：逐 token 推送，使用 SSE 格式"""
    def generate():
        for chunk in run_agent_stream(req.question):
            # SSE 格式：每行以 "data: " 开头，两个换行结尾
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")


class AddRequest(BaseModel):
    note: str

@app.post("/add")
def add_endpoint(req: AddRequest):
    result = add_note(req.note)
    return {"message": result}
