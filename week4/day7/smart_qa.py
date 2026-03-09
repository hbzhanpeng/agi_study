"""
Week 4 Day 7 大实战：智能文档问答系统（整合全周技巧）
目标：一个完整的 RAG 系统，支持多种检索策略 + 自动评估
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
# 知识库（比之前更丰富）
# ============================================================
DOCUMENTS = [
    "公司年假政策：入职满1年的员工享有15天年假，入职满5年享有20天年假。年假需提前3天申请，需直属领导审批。未休完的年假不可累积到下一年。",
    "报销流程：员工需在费用发生后30天内提交报销申请。单笔500元以下由部门经理审批，500元以上需总监审批。报销需附发票原件。差旅报销需额外提供出差审批单。",
    "远程办公政策：每周最多2天远程办公，需提前1天在OA系统申请。远程办公日必须保持即时通讯在线，参加所有已安排的会议。试用期员工不可申请远程办公。",
    "试用期规定：新员工试用期为3个月，试用期工资为正式工资的80%。试用期内公司和员工均可随时解除劳动合同，需提前3天通知。试用期不享有年假和远程办公权利。",
    "加班政策：工作日加班需提前申请，每日加班不超过3小时。加班可选择调休或按1.5倍工资计算。周末加班按2倍工资计算，法定节假日加班按3倍工资计算。",
    "培训制度：公司每季度组织一次技术培训，每年提供每人5000元培训基金。员工可自主选择外部培训课程，凭结业证书报销。培训期间算正常出勤。",
    "晋升制度：公司每半年进行一次绩效评估，评估结果分为A（优秀）、B（良好）、C（合格）、D（不合格）。连续两次A级评估可获得晋升机会，连续两次D级将进入绩效改进计划。",
]


# ============================================================
# 基础工具函数
# ============================================================
def call_llm(prompt, temperature=0, max_tokens=200):
    """统一的 LLM 调用函数"""
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-ai/DeepSeek-V2.5",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        },
        timeout=30
    )
    return resp.json()["choices"][0]["message"]["content"].strip()


def get_embedding(texts):
    """获取文本 Embedding"""
    resp = requests.post(
        f"{BASE_URL}/embeddings",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": "BAAI/bge-large-zh-v1.5", "input": texts, "encoding_format": "float"},
        timeout=30
    )
    return [item["embedding"] for item in resp.json()["data"]]


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# 预计算文档 Embedding
print("🔢 正在建立知识库索引...")
doc_embeddings = get_embedding(DOCUMENTS)
print(f"  ✅ 完成！{len(DOCUMENTS)} 篇文档 × {len(doc_embeddings[0])} 维向量")


# ============================================================
# 核心检索函数
# ============================================================
def vector_search(query_text, top_k=3):
    """向量检索"""
    query_emb = get_embedding([query_text])[0]
    scores = [cosine_similarity(emb, query_emb) for emb in doc_embeddings]
    top_idx = np.argsort(scores)[::-1][:top_k]
    return [{"chunk": DOCUMENTS[i], "score": round(scores[i], 4)} for i in top_idx]


# ============================================================
# TODO 1: 实现智能路由函数
# ============================================================
# 根据用户问题的特点，自动选择最佳检索策略
# 这就是 Self-RAG 的简化版
def smart_route(question):
    """
    判断用户问题应该用哪种策略：
    - "direct": 不需要检索，LLM 直接回答（如"1+1等于几"）
    - "rewrite": 口语化问题，需要先改写再检索
    - "normal": 正常问题，直接检索
    
    TODO: 实现判断逻辑
    提示：
    - 如果问题里包含公司/年假/加班/报销等关键词 → "normal"
    - 如果问题很短且包含"咋""啥""咋整""不" → "rewrite"
    - 其他情况（如数学题、闲聊）→ "direct"
    """
    if any(keyword in question for keyword in ["公司", "年假", "加班", "报销", "试用", "远程", "培训", "晋升", "工资"]):
        return "normal"
    if any(keyword in question for keyword in ["咋", "啥", "不", "吗", "呢", "啊"]):
        return "rewrite"
    return "direct"


# ============================================================
# TODO 2: 实现完整的问答管线
# ============================================================
def ask(question):
    """
    完整的智能问答管线：
    1. 用 smart_route 判断策略
    2. 根据策略执行不同的处理流程
    3. 返回回答和元数据
    
    TODO: 实现完整流程
    提示参考下面的伪代码：
    
    route = smart_route(question)
    if route == "direct":
        answer = call_llm(question)
        return {"answer": answer, "strategy": "direct", "sources": []}
    
    if route == "rewrite":
        # 调用 call_llm 改写问题
        rewritten = call_llm(f"请将以下口语化问题改写为专业查询，只返回改写结果：{question}")
        search_query = rewritten
    else:
        search_query = question
    
    results = vector_search(search_query, top_k=2)
    context = "\n".join([r["chunk"] for r in results])
    
    # 用 RAG prompt 生成回答（记得加角色+参考资料+兜底规则）
    prompt = ???
    answer = call_llm(prompt, max_tokens=300)
    
    return {"answer": answer, "strategy": route, "sources": results}
    """
    route = smart_route(question)
    if route == "direct":
        answer = call_llm(question)
        return {"answer": answer, "strategy": "direct", "sources": []}
    if route == "rewrite":
        rewritten = call_llm(f"请将以下口语化问题改写成专业查询，只返回改写结果：{question}")
        search_query = rewritten
    else:
        search_query = question
    results = vector_search(search_query, top_k=2)
    context = "\n".join([r["chunk"] for r in results])
    
    # 用 RAG prompt 生成回答（记得加角色+参考资料+兜底规则）
    prompt = f"""
    你是一个专业的文档问答助手，请根据参考资料回答用户问题。
    如果参考资料中没有相关信息，请回答"我不确定，建议咨询HR"。
    
    用户问题：{question}
    参考资料：{context}
    """
    answer = call_llm(prompt, max_tokens=300)
    
    return {"answer": answer, "strategy": route, "sources": results}


# ============================================================
# TODO 3: 实现批量评估函数
# ============================================================
def evaluate(test_cases):
    """
    批量评估 RAG 系统
    
    TODO: 遍历 test_cases，对每个测试用例：
    1. 调用 ask() 获取回答
    2. 检查回答中是否包含 expected_answer
    3. 统计正确率
    
    提示：复用 Day 6 的评估逻辑
    """
    correct = 0
    total = len(test_cases)
    for tc in test_cases:
        result = ask(tc["question"])
        hit = tc["expected_answer"] in result["answer"]
        correct += 1 if hit else 0
        print(f"  {'✅' if hit else '❌'} {tc['question']} → {'命中' if hit else '未命中'} '{tc['expected_answer']}'")
    accuracy = correct / total
    print(f"\n  📊 总准确率: {correct}/{total} = {accuracy:.0%}")
    return {"accuracy": accuracy, "total": total, "correct": correct}


# ============================================================
# 测试（不需要修改）
# ============================================================
TEST_CASES = [
    {"question": "入职3年有多少天年假？", "expected_answer": "15"},
    {"question": "年假咋整啊？", "expected_answer": "年假"},
    {"question": "加班给钱不？", "expected_answer": "1.5倍"},
    {"question": "试用期工资打几折？", "expected_answer": "80%"},
    {"question": "培训基金多少钱？", "expected_answer": "5000"},
    {"question": "1+1等于几？", "expected_answer": "2"},
]

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🤖 智能文档问答系统")
    print("=" * 60)
    
    for tc in TEST_CASES:
        q = tc["question"]
        print(f"\n❓ {q}")
        result = ask(q)
        print(f"  🧭 策略: {result['strategy']}")
        print(f"  💡 回答: {result['answer'][:80]}")
        if result['sources']:
            print(f"  📊 相似度: {[r['score'] for r in result['sources']]}")
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("📊 自动化评估")
    print("=" * 60)
    evaluate(TEST_CASES)
