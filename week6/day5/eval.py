import requests
# from rag import ask, call_llm
from config import API_KEY, CHAT_MODEL
from agent import run_agent
from inference import load_model, ask
import os
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(_BASE_DIR, "train.json")

eval_data = [
    {
        "question": "切文档的时候内容断掉了怎么解决", 
        "expected": "使用overlap分片"
    },
    {
        "question": "prompt有空格检索不到结果怎么办",
        "expected": "不要添加空行或者空格；或者使用textWrap.dedent解决"
    },
    {
        "question": "用户问法和知识库存储方式语义不匹配怎么办",
        "expected": "用HyDE，先让 LLM 生成假设答案，用答案去检索答案，相似度更高"
    },
    {
        "question": "上下文和内容之间缺少空行导致 LLM 理解错误怎么办",
        "expected": "【上下文】后加 \n\n 空行分隔，让 LLM 正确识别内容边界"
    },
    {
        "question": "多轮对话 history 的 role 字段用了 'ai'怎么办",
        "expected": "前端存 history 时统一用 'assistant'"
    },
    {
        "question": "长对话 token 爆炸怎么办",
        "expected": "超过 10 轮后用 LLM 压缩为摘要，保留最近 2 轮原文"
    },
    {
        "question": "Agent 和 RAG 的本质区别是什么",
        "expected": "RAG 是写死的流水线，Agent 是 LLM 自主决策"
    },
    {
        "question": "Agent 行为边界不清晰，知识库没有内容时 LLM 自己补充回答怎么办",
        "expected": "在 system prompt 里明确：知识库有内容才回答，没有则告知用户"
    }
]

def evaluate(eval_data: list) -> dict:
    results = []
    
    for item in eval_data:
        # 1. 调用系统得到回答
        try:
            answer = run_agent(item["question"])
        except Exception as e:
            answer = f"[错误] {e}"
        
        # 2. 用 LLM 判断回答是否包含期望答案
        judge_prompt = (
            "判断以下系统回答是否包含了期望答案的核心内容，只回答'是'或'否'：\n\n"
            f"期望答案：{item['expected']}\n\n"
            f"系统回答：{answer}"
        )
        judgement = call_llm(judge_prompt, max_tokens=10)
        correct = "是" in judgement
        
        results.append({
            "question": item["question"],
            "correct": correct,
            "answer": answer[:100]  # 只显示前100字
        })
        print(f"{'✅' if correct else '❌'} {item['question'][:20]}...")
        print(f"   期望: {item['expected'][:50]}")
        print(f"   回答: {answer[:100]}")
        print(f"   判断: {judgement}")
        print()
    score = sum(r["correct"] for r in results) / len(results)
    print(f"\n总分: {score*100:.1f}% ({sum(r['correct'] for r in results)}/{len(results)})")
    return {"score": score, "results": results}


if __name__ == "__main__":
    # evaluate(eval_data)
    print("加载模型中...")
    model, tokenizer = load_model()
    
    # 从train.json加载数据
    import json
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 测试前3条，对比输出和期望答案
    for item in data[:3]:
        question = item["instruction"]
        expected = item["output"]
        actual = ask(question, model, tokenizer)
        
        print(f"\n问题：{question}")
        print(f"\n期望：{expected}")
        print(f"\n实际：{actual}")
        print("\n" + "="*50)
