import sys
import io
import requests
import json
import os
import chromadb
from config import API_KEY, LLM_BASE_URL, EMBED_BASE_URL, EMBED_MODEL, CHAT_MODEL, CHUNK_SIZE, CHUNK_OVERLAP

# Windows 控制台 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


import os as _os
# 初始化数据库（使用绝对路径，不受运行目录影响）
_dir = _os.path.dirname(_os.path.abspath(__file__))
db = chromadb.PersistentClient(path=_os.path.join(_dir, "chroma_db"))
collection = db.get_or_create_collection("my_docs")

def get_embedding(texts: list[str]) -> list[list[float]]:
    """调用 SiliconFlow embedding API，返回向量列表"""
    resp = requests.post(
        f"{EMBED_BASE_URL}/embeddings",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": EMBED_MODEL, "input": texts, "encoding_format": "float"},
        timeout=60
    )
    return [item["embedding"] for item in resp.json()["data"]]

def call_llm(prompt: str, max_tokens: int = 500, history: list = None) -> str:
    """调用 LLM，返回完整字符串（非流式，供内部使用）"""
    if history is None:
        history = []
    try:
        resp = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": CHAT_MODEL,
                "messages": history + [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": max_tokens
            },
            timeout=120
        )
        answer = resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"调用 LLM 失败: {e}")
        answer = "抱歉，我暂时无法回答这个问题。"
    return answer

def call_llm_stream(messages: list, max_tokens: int = 500, tools: list = None, tool_choice: str = None):
    """调用 LLM 流式版本，逐 token yield 文字片段（供最终回答使用）
    
    传入含 tool_calls 的 history 时，需要同时传 tools + tool_choice='none'，
    否则 LLM 会返回 content: null
    """
    try:
        body = {
            "model": CHAT_MODEL,
            "messages": messages,
            "temperature": 0,
            "max_tokens": max_tokens,
            "stream": True
        }
        if tools:
            body["tools"] = tools
        if tool_choice:
            body["tool_choice"] = tool_choice

        resp = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json=body,
            timeout=120,
            stream=True
        )
        for line in resp.iter_lines():
            if line:
                line_text = line.decode("utf-8")
                if line_text.startswith("data: "):
                    data_str = line_text[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        content = data["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except Exception:
                        continue
    except Exception as e:
        print(f"流式 LLM 调用失败: {e}")
        yield "抱歉，我暂时无法回答这个问题。"


def index_docs(docs_folder: str) -> None:
    """读取文件夹里所有 .txt 文件，分片向量化后存入数据库"""
    if collection.count() > 0:
        print(f"数据库已有 {collection.count()} 条数据，跳过索引。")
        return

    # 读取所有文件
    text = ""
    for filename in os.listdir(docs_folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(docs_folder, filename)
            with open(filepath, "r", encoding='utf-8') as f:
                text += f.read()

    # 分片（固定大小 + overlap）
    step = CHUNK_SIZE - CHUNK_OVERLAP
    chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), step)]

    # 向量化并存入数据库
    embeddings = get_embedding(chunks)
    collection.add(
        ids=[str(i) for i in range(len(chunks))],
        embeddings=embeddings,
        documents=chunks
    )
    print(f"索引完成，共 {len(chunks)} 个 chunk。")

def rewrite_question(question: str, history: list) -> str:
    """结合历史记录，把模糊的问题改写成完整的问题"""
    prompt = (
        "根据对话历史，将下面这个模糊的问题改写成一个完整清晰的问题，只返回改写后的问题，不要解释：\n\n"
        f"{question}"
    )
    return call_llm(prompt, max_tokens=500, history=history)

def get_hypothetical_answer(question: str) -> str:
    """根据问题生成假设答案"""
    prompt = (
        "请根据以下问题，生成一个可能的答案（不需要准确，只需要语义相关）：\n"
        f"【问题】\n{question}"
    )

    return call_llm(prompt, max_tokens=100)

def summarize_history(history: list) -> list:
    if len(history) <= 20:
        return history  # 不超过10轮，直接返回
    
    # 超过10轮，压缩前面的部分
    to_summarize = history[:-4]   # 除了最近2轮，其余都压缩
    last_4 = history[-4:]         # 保留最近2轮原文
    
    # 用LLM生成摘要
    prompt = (
    "请将以下对话历史压缩成一段简洁的摘要，保留关键信息：\n\n"
    f"{to_summarize}"
    )   
    summary = call_llm(prompt, max_tokens=200)
    
    return [{"role": "system", "content": f"对话摘要：{summary}"}] + last_4

        

def ask(question: str, history: list = None, use_hyde: bool = True) -> str:
    """向量检索 + LLM 回答，返回答案和来源"""
    # 第一步：改写问题
    if history is None:
        history = []
    history = summarize_history(history)  # 加这行
    question = rewrite_question(question, history)

    # 第二步：用假设答案做检索（不是用原始问题）
    # 检索最相关的 chunk
    if use_hyde:
        # 获取假设答案
        hypothetical_answer = get_hypothetical_answer(question)
        results = collection.query(
            query_embeddings=get_embedding([hypothetical_answer]),
            n_results=3
        )
    else:
        results = collection.query(
            query_embeddings=get_embedding([question]),
            n_results=3
        )

    context = "\n\n".join(results["documents"][0])
    prompt = (
        "你是用户的个人踩坑知识库助手。以下是从知识库中检索到的相关笔记，请基于笔记内容回答用户问题。\n"
        "笔记格式为【问题】【原因】【解决】，请提取其中的解决方案来回答。\n"
        "如果所有笔记均与问题完全无关，才说'你的知识库里还没有这条记录'。\n\n"
        "【知识库笔记】\n\n"
        f"{context}\n\n"
        "【用户问题】\n\n"
        f"{question}"
    )

    # 调用 LLM
    answer = call_llm(prompt, history=history)
    # 拼接来源
    sources = "\n".join([
        f"- 笔记 #{results['ids'][0][i]}  相似度: {results['distances'][0][i]:.3f}\n  预览: {results['documents'][0][i][:80]}..."
        for i in range(len(results["ids"][0]))
    ])
    return answer, sources

# 命令行调用：自己读输入
def add_note_interactive() -> None:
    lines = []
    while True:
        line = input("> ")
        if line.strip().upper() == "END":
            break
        lines.append(line)
    note = "\n".join(lines)
    add_note(note)  # 复用核心逻辑

def add_note(note: str) -> None:
    """将新笔记向量化后存入数据库"""
    embeddings = get_embedding([note])
    collection.add(
        ids=[str(collection.count())],
        embeddings=embeddings,
        documents=[note]
    )
    print(f"笔记已添加，ID: {collection.count()-1}")
    return f"笔记已添加，ID: {collection.count()-1}"

if __name__ == "__main__":
    # python rag.py add     → 进入添加笔记模式
    # python rag.py ask "问题"  → 直接提问
    if len(sys.argv) < 2:
        print("使用说明：")
        print("  python rag.py add     → 进入添加笔记模式")
        print("  python rag.py ask \"问题\"  → 直接提问")
        sys.exit(1)
    if sys.argv[1] == "add":
        add_note_interactive()
    elif sys.argv[1] == "ask":
        history = []
        while True:
            question = input("你: ")
            if question.strip().upper() == "END":
                break
            answer, sources = ask(question, history)
            print(f"AI: {answer}\n{sources}")
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})