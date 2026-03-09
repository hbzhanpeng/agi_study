"""
Week 4 Day 6 实战：RAG 评估体系
目标：用代码自动化评估 RAG 系统的检索和回答质量
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
API_KEY = os.getenv("SILICONFLOW_API_KEY")
BASE_URL = "https://api.siliconflow.cn/v1"


# ============================================================
# 准备测试数据集（人工标注的"标准答案"）
# ============================================================
TEST_SET = [
    {
        "question": "入职3年有多少天年假？",
        "expected_answer": "15天",
        "expected_doc_keyword": "年假"
    },
    {
        "question": "加班工资怎么算？",
        "expected_answer": "1.5倍",
        "expected_doc_keyword": "加班"
    },
    {
        "question": "远程办公一周最多几天？",
        "expected_answer": "2天",
        "expected_doc_keyword": "远程"
    },
    {
        "question": "试用期工资是正式的百分之多少？",
        "expected_answer": "80%",
        "expected_doc_keyword": "试用期"
    },
]


# ============================================================
# 复用 Day 4 的核心函数
# ============================================================
DOCUMENTS = [
    "公司年假政策：入职满1年的员工享有15天年假，入职满5年享有20天年假。年假需提前3天申请，需直属领导审批。",
    "报销流程：员工需在费用发生后30天内提交报销申请。单笔500元以下由部门经理审批，500元以上需总监审批。报销需附发票原件。",
    "远程办公政策：每周最多2天远程办公，需提前1天在OA系统申请。远程办公日必须保持即时通讯在线，参加所有已安排的会议。",
    "试用期规定：新员工试用期为3个月，试用期工资为正式工资的80%。试用期内公司和员工均可随时解除劳动合同，需提前3天通知。",
    "加班政策：工作日加班需提前申请，每日加班不超过3小时。加班可选择调休或按1.5倍工资计算。周末加班按2倍工资计算。",
]

def get_embedding(texts):
    resp = requests.post(
        f"{BASE_URL}/embeddings",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": "BAAI/bge-large-zh-v1.5", "input": texts, "encoding_format": "float"},
        timeout=30
    )
    data = resp.json()
    return [item["embedding"] for item in data["data"]]

print("🔢 正在生成文档 Embedding...")
chunk_embeddings = get_embedding(DOCUMENTS)
print("  ✅ 完成")

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search(query, top_k=2):
    query_emb = get_embedding([query])[0]
    scores = [cosine_similarity(emb, query_emb) for emb in chunk_embeddings]
    top_idx = np.argsort(scores)[::-1][:top_k]
    return [{"chunk": DOCUMENTS[i], "score": scores[i]} for i in top_idx]

def rag_answer(question):
    results = search(question, top_k=2)
    context = "\n".join([r["chunk"] for r in results])
    prompt = f"你是企业知识库助手。根据参考资料简短回答问题，一句话即可。\n参考资料：{context}\n问题：{question}"
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": "deepseek-ai/DeepSeek-V2.5", "messages": [{"role": "user", "content": prompt}], "temperature": 0, "max_tokens": 100},
        timeout=30
    )
    return {"answer": resp.json()["choices"][0]["message"]["content"], "results": results}


# ============================================================
# TODO 1: 实现 Context Relevance 评估
# ============================================================
# 检查检索到的文档是否包含期望的关键词
def eval_context_relevance(test_item, search_results):
    # TODO: 检查 search_results 中的文档是否包含 test_item["expected_doc_keyword"]
    # 返回 1（命中）或 0（未命中）
    # 提示：遍历 search_results，检查每个 result["chunk"] 是否包含关键词
    for result in search_results:
        if test_item["expected_doc_keyword"] in result["chunk"]:
            return 1
    return 0


# ============================================================
# TODO 2: 实现 Answer Relevance 评估
# ============================================================
# 检查模型回答是否包含期望的答案关键信息
def eval_answer_relevance(test_item, answer):
    # TODO: 检查 answer 中是否包含 test_item["expected_answer"]
    # 返回 1（包含）或 0（不包含）
    if test_item["expected_answer"] in answer:
        return 1
    return 0


# ============================================================
# 评估主函数（不需要修改）
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📊 RAG 系统自动化评估")
    print("=" * 60)
    
    context_scores = []
    answer_scores = []
    
    for item in TEST_SET:
        q = item["question"]
        print(f"\n❓ {q}")
        
        # 获取 RAG 回答
        result = rag_answer(q)
        print(f"  💡 回答: {result['answer'][:60]}")
        
        # 评估 Context Relevance
        cr = eval_context_relevance(item, result["results"])
        context_scores.append(cr)
        print(f"  📚 Context Relevance: {'✅' if cr else '❌'}")
        
        # 评估 Answer Relevance
        ar = eval_answer_relevance(item, result["answer"])
        answer_scores.append(ar)
        print(f"  🎯 Answer Relevance: {'✅' if ar else '❌'}")
    
    print("\n" + "=" * 60)
    print("📊 评估报告")
    print("=" * 60)
    print(f"  Context Relevance（检索准确率）: {sum(context_scores)}/{len(context_scores)} = {sum(context_scores)/len(context_scores):.0%}")
    print(f"  Answer Relevance（回答准确率）:  {sum(answer_scores)}/{len(answer_scores)} = {sum(answer_scores)/len(answer_scores):.0%}")
    print(f"\n  {'🎉 效果优秀！' if sum(context_scores)/len(context_scores) >= 0.75 else '⚠️ 需要优化检索策略'}")
