"""
Week 4 Day 4 实战：完整 RAG 系统
目标：从文档加载 → 分块 → Embedding → 存储 → 检索 → 生成回答
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import json
import numpy as np
import requests
from dotenv import load_dotenv

# 加载 API Key
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
API_KEY = os.getenv("SILICONFLOW_API_KEY")
BASE_URL = "https://api.siliconflow.cn/v1"

# ============================================================
# 阶段 1: 准备文档（模拟企业知识库）
# ============================================================
DOCUMENTS = [
    "公司年假政策：入职满1年的员工享有15天年假，入职满5年享有20天年假。年假需提前3天申请，需直属领导审批。",
    "报销流程：员工需在费用发生后30天内提交报销申请。单笔500元以下由部门经理审批，500元以上需总监审批。报销需附发票原件。",
    "远程办公政策：每周最多2天远程办公，需提前1天在OA系统申请。远程办公日必须保持即时通讯在线，参加所有已安排的会议。",
    "试用期规定：新员工试用期为3个月，试用期工资为正式工资的80%。试用期内公司和员工均可随时解除劳动合同，需提前3天通知。",
    "加班政策：工作日加班需提前申请，每日加班不超过3小时。加班可选择调休或按1.5倍工资计算。周末加班按2倍工资计算。",
]

print("📄 阶段 1: 文档准备完成")
print(f"  共 {len(DOCUMENTS)} 篇文档")


# ============================================================
# 阶段 2: 文本分块（这里文档已经很短，实际项目需要 Chunking）
# ============================================================
# 实际项目中这里要做递归分块，我们的示例文档已经是小块了
chunks = DOCUMENTS.copy()
print(f"\n📦 阶段 2: 分块完成，共 {len(chunks)} 个 chunk")


# ============================================================
# 阶段 3: Embedding（调用 BGE 模型把文本变成向量）
# ============================================================
def get_embedding(texts):
    """调用硅基流动 BGE 模型获取 Embedding"""
    resp = requests.post(
        f"{BASE_URL}/embeddings",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "BAAI/bge-large-zh-v1.5",
            "input": texts,
            "encoding_format": "float"
        },
        timeout=30
    )
    data = resp.json()
    if resp.status_code != 200 or "data" not in data or data["data"] is None:
        print(f"  ❌ API 错误: status={resp.status_code}")
        print(f"  响应: {json.dumps(data, ensure_ascii=False)[:300]}")
        print(f"  API Key: {API_KEY[:8] if API_KEY else 'None'}...")
        sys.exit(1)
    return [item["embedding"] for item in data["data"]]

print("\n🔢 阶段 3: 正在生成 Embedding...")
chunk_embeddings = get_embedding(chunks)
print(f"  ✅ 完成！每个 chunk 变成了 {len(chunk_embeddings[0])} 维向量")


# ============================================================
# TODO 1: 实现余弦相似度函数
# ============================================================
# 提示：cos_sim = (A · B) / (||A|| × ||B||)
# np.dot() 算点积，np.linalg.norm() 算向量长度
def cosine_similarity(vec_a, vec_b):
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))


# ============================================================
# TODO 2: 实现检索函数（找最相似的 Top K 文档）
# ============================================================
def search(query, top_k=3):
    # Step 1: 把用户问题也变成 Embedding
    query_embedding = get_embedding([query])[0]
    
    # Step 2: 计算和每个 chunk 的相似度
    # 提示：遍历 chunk_embeddings，调用 cosine_similarity
    scores = [cosine_similarity(chunk_embedding, query_embedding) for chunk_embedding in chunk_embeddings]
    
    # Step 3: 按相似度排序，返回 Top K
    # 提示：用 np.argsort() 排序，取最后 K 个（最大的）
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append({
            "chunk": chunks[idx],
            "score": scores[idx]
        })
    return results


# ============================================================
# RAG 生成函数
# ============================================================
def rag_answer(question):
    results = search(question, top_k=2)
    context = "\n".join([r["chunk"] for r in results])
    
    prompt = f"""
        你是一个企业知识库助手，请根据以下参考资料回答用户问题。
        如果参考资料中没有相关信息，请回答"我不确定，建议咨询HR"。

        参考资料：
        {context}

        用户问题：{question}
    """
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-ai/DeepSeek-V2.5",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 500
        },
        timeout=30
    )
    answer = resp.json()["choices"][0]["message"]["content"]
    
    return {
        "question": question,
        "answer": answer,
        "sources": [r["chunk"][:30] + "..." for r in results],
        "scores": [round(r["score"], 4) for r in results]
    }


# ============================================================
# TODO 4: 实现 Query 改写函数
# ============================================================
def rewrite_query(question):
    # Query 改写的 prompt：让 LLM 把口语问题改写成专业查询
    # 注意：这里不需要 context！改写只处理问题本身
    prompt = f"请将以下口语化问题改写为一个清晰、专业的企业知识库搜索查询。只返回改写后的查询，不要任何解释。\n原始问题：{question}\n改写后的查询："

    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-ai/DeepSeek-V2.5",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 100
        },
        timeout=30
    )
    return resp.json()["choices"][0]["message"]["content"].strip()


def rag_answer_with_rewrite(question):
    rewritten = rewrite_query(question)
    print(f"  🔄 改写: '{question}' → '{rewritten}'")
    return rag_answer(rewritten)


# ============================================================
# TODO 5: 实现 HyDE（假设性文档嵌入）
# ============================================================
# 核心思路：先让 LLM 生成一个"假回答"，用假回答去检索
def hyde_search(question, top_k=2):
    # TODO: 设计一个 prompt，让 LLM 生成一个假设性的回答
    # 注意：这个回答不需要正确，只需要格式像真文档
    prompt = f"假设你是一个企业HR，请简短回答以下问题：{question}"

    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-ai/DeepSeek-V2.5",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 200
        },
        timeout=30
    )
    fake_answer = resp.json()["choices"][0]["message"]["content"].strip()
    print(f"  📝 假回答: {fake_answer[:60]}...")
    
    # 用假回答去检索（而不是用原始问题）
    return search(fake_answer, top_k=top_k)


def rag_answer_with_hyde(question):
    results = hyde_search(question, top_k=2)
    context = "\n".join([r["chunk"] for r in results])
    
    prompt = f"""
        你是一个企业知识库助手，请根据以下参考资料回答用户问题。
        如果参考资料中没有相关信息，请回答"我不确定，建议咨询HR"。
        参考资料：
        {context}
        用户问题：{question}
    """
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-ai/DeepSeek-V2.5",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 500
        },
        timeout=30
    )
    answer = resp.json()["choices"][0]["message"]["content"]
    return {
        "answer": answer,
        "scores": [round(r["score"], 4) for r in results]
    }


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🧪 测试: 三种方式对比（普通 vs Query改写 vs HyDE）")
    print("=" * 50)
    
    for q in ["年假咋整啊？", "加班给钱不？"]:
        print(f"\n❓ 口语问题: {q}")
        
        print("  --- 1. 普通 RAG ---")
        r1 = rag_answer(q)
        print(f"  📊 相似度: {r1['scores']}")
        
        print("  --- 2. Query 改写 ---")
        r2 = rag_answer_with_rewrite(q)
        print(f"  📊 相似度: {r2['scores']}")
        
        print("  --- 3. HyDE ---")
        r3 = rag_answer_with_hyde(q)
        print(f"  📊 相似度: {r3['scores']}")
        
        print("-" * 40)
