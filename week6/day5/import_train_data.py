# import_train_data.py - 将 train.json 中的笔记同步到向量数据库
import json
import os
import chromadb
from rag import get_embedding

# ===== 1. 配置 =====
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(_BASE_DIR, "train.json")
CHROMA_PATH = os.path.join(_BASE_DIR, "chroma_db")

def main():
    # 建立数据库连接
    db = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = db.get_or_create_collection("my_docs")
    
    # 读取训练数据
    print(f"正在读取 {DATA_PATH}...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        train_data = json.load(f)
    
    # 提取所有笔记内容 (output 字段)
    all_notes = [item["output"] for item in train_data]
    print(f"共发现 {len(all_notes)} 条笔记。")

    # 为了防止重复和数据混乱，我们先清空当前 collection (慎用，仅限本项目学习)
    print("正在清空旧数据...")
    # 获取所有 ID 并删除
    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)
    
    # 批量向量化并存入
    print("正在同步新数据到 ChromaDB (调用 Embedding API)...")
    
    # 分片处理，防止一次性请求太多
    batch_size = 10
    for i in range(0, len(all_notes), batch_size):
        batch_notes = all_notes[i : i + batch_size]
        print(f"正在处理第 {i} 到 {min(i+batch_size, len(all_notes))} 条...")
        
        embeddings = get_embedding(batch_notes)
        collection.add(
            ids=[str(j) for j in range(i, i + len(batch_notes))],
            embeddings=embeddings,
            documents=batch_notes
        )
    
    print(f"✅ 同步完成！当前数据库共有 {collection.count()} 条记录。")

if __name__ == "__main__":
    main()
