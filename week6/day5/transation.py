
import chromadb
import json
import os as _os

_dir = _os.path.dirname(_os.path.abspath(__file__))
db = chromadb.PersistentClient(path=_os.path.join(_dir, "chroma_db"))
collection = db.get_or_create_collection("my_docs")

# 读出所有笔记
result = collection.get()

alpaca_data = []
for doc in result["documents"]:
    # 从笔记里提取【问题】那行作为 instruction
    lines = doc.split("\n")
    instruction = ""
    for line in lines:
        if line.startswith("【问题】"):
            instruction = line.replace("【问题】", "").strip()
            break
    
    if instruction:  # 只处理有【问题】的笔记
        alpaca_data.append({
            "instruction": instruction,
            "input": "",
            "output": doc
        })
seen = set()
unique_data = []
for item in alpaca_data:
    if item["instruction"] not in seen:
        seen.add(item["instruction"])
        unique_data.append(item)

# 保存
with open("train.json", "w", encoding="utf-8") as f:
    json.dump(unique_data, f, ensure_ascii=False, indent=2)


print(f"共生成 {len(unique_data)} 条训练数据")