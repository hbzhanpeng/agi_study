import sys
import io
import requests
import os
import chromadb
from dotenv import load_dotenv

# Windows 控制台 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'week4', '.env'))
API_KEY = os.getenv("SILICONFLOW_API_KEY")
BASE_URL = "https://api.siliconflow.cn/v1"
CHUNK_SIZE = 500    # 每个 chunk 的字符数
CHUNK_OVERLAP = 100 # chunk 间重叠字符数
EMBED_MODEL = "BAAI/bge-large-zh-v1.5"
CHAT_MODEL = "deepseek-ai/DeepSeek-V2.5"

# 初始化数据库
db = chromadb.PersistentClient(path="./chroma_db")
collection = db.get_or_create_collection("my_docs")


def get_embedding(texts: list[str]) -> list[list[float]]:
    """调用 SiliconFlow embedding API，返回向量列表"""
    resp = requests.post(
        f"{BASE_URL}/embeddings",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": EMBED_MODEL, "input": texts, "encoding_format": "float"},
        timeout=30
    )
    return [item["embedding"] for item in resp.json()["data"]]


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


def ask(question: str) -> str:
    """向量检索 + LLM 回答，返回答案和来源"""
    # 检索最相关的 chunk
    results = collection.query(
        query_embeddings=get_embedding([question]),
        n_results=3
    )

    context = "\n\n".join(results["documents"][0])
    prompt = f"""你是一位专业的AI技术顾问，仅基于以下上下文回答问题，不要编造信息。
    如果上下文没有相关答案，请明确说明"无法从提供的信息中找到答案"。

    【上下文】
    {context}

    【问题】
    {question}"""

    # 调用 LLM
    try:
        resp = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": CHAT_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 300
            },
            timeout=30
        )
        answer = resp.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        return f"请求失败: {e}"

    # 拼接来源
    sources = "\n".join([
        f"- 笔记 #{results['ids'][0][i]}  相似度: {results['distances'][0][i]:.3f}\n  预览: {results['documents'][0][i][:80]}..."
        for i in range(len(results["ids"][0]))
    ])
    return f"{answer}\n\n【来源】\n{sources}"

if __name__ == "__main__":
    index_docs("./docs")
    print(ask("RAG 里 results 忘记传给 LLM 怎么办"))