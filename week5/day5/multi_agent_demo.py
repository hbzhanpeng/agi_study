"""
Week 5 Day 5 实战：从零手写 Multi-Agent (程序员 vs 审查员)
目标：体验最经典的“双子星”结构（消息传递通信协议）
"""
import sys
import io
import os
import requests
from dotenv import load_dotenv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'week4', '.env'))
API_KEY = os.getenv("SILICONFLOW_API_KEY")
BASE_URL = "https://api.siliconflow.cn/v1"

# ============================================================
# 基础大模型调用封装
# ============================================================
def call_llm(messages, temperature=0.7):
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-ai/DeepSeek-V2.5",
            "messages": messages,
            "temperature": temperature,
        },
        timeout=60
    )
    return resp.json()["choices"][0]["message"]["content"].strip()


# ============================================================
# TODO 1: 定义两个不同角色的 Agent (其实就是不同 System Prompt 的包装)
# ============================================================
class CoderAgent:
    def __init__(self):
        self.system_msg = {
            "role": "system",
            # 提示：扮演资深 Python 程序员，只输出代码，不需要解释
            "content": "你是一个资深 Python 程序员。请根据需求编写高效、优雅的代码。只输出代码本身，绝不要输出任何多余的解释文字或 Markdown 标记块。"
        }
        self.history = [self.system_msg]

    def generate_code(self, requirement, feedback=None):
        if feedback:
            self.history.append({"role": "user", "content": f"Review意见：\n{feedback}\n请根据意见修改代码。"})
        else:
            self.history.append({"role": "user", "content": f"需求：\n{requirement}"})
            
        print("💻 [Coder] 正在激情打字写代码...")
        code_result = call_llm(self.history)
        self.history.append({"role": "assistant", "content": code_result})
        return code_result

class ReviewerAgent:
    def __init__(self):
        self.system_msg = {
            "role": "system",
            # 提示：扮演严苛的代码审查员，寻找 Bug、安全隐患、性能问题。
            # 必须用 JSON 格式返回结果 {"approved": true/false, "comments": "具体的意见"}
            "content": "你是一个极其严苛的高级代码审查员。你的任务是找出代码中的 Bug、不符合要求的实现以及时间复杂度过高的问题。你必须、绝对只能返回一段合法的 JSON，格式为 {\"approved\": true或false, \"comments\": \"你的具体审查意见和指导\"}。不要输出任何其他文本！"
        }
        self.history = [self.system_msg]

    def review_code(self, code_to_review):
        self.history.append({"role": "user", "content": f"请审查这段代码：\n{code_to_review}"})
        print("🧐 [Reviewer] 戴上眼镜开始挑刺...")
        review_result = call_llm(self.history, temperature=0.1) # 评审需要严谨，温度低
        self.history.append({"role": "assistant", "content": review_result})
        
        # 简单解析 JSON
        import json
        try:
            start = review_result.find("{")
            end = review_result.rfind("}") + 1
            return json.loads(review_result[start:end])
        except:
            return {"approved": False, "comments": "解析评审结果失败，请重试。"}

# ============================================================
# TODO 2: 实现通信协议主循环 (消息传递 Message Passing)
# ============================================================
def run_multi_agent_company(requirement, max_rounds=3):
    """
    这就是典型的“消息传递 (Message Passing)”通信协议的实现机制
    Coder 和 Reviewer 互相把消息扔给对方，如果被拒就重写，通过就下班。
    """
    coder = CoderAgent()
    reviewer = ReviewerAgent()
    
    current_code = None
    feedback = None
    
    print(f"🎯 任务下达：{ requirement}")
    print("=" * 50)
    
    for round_idx in range(1, max_rounds + 1):
        print(f"\n🌀 --- 第 {round_idx} 轮研发 ---")
        
        # 1. 程序员根据需求（或反馈）写代码
        current_code = coder.generate_code(requirement, feedback)
        print(f"📦 [Coder] 提交的代码片段:\n{current_code[:150]}...\n")
        
        # 2. 审查员审阅刚刚生成的代码
        review_decision = reviewer.review_code(current_code)
        is_approved = review_decision.get("approved", False)
        feedback = review_decision.get("comments", "无意见")
        
        if is_approved:
            print("🎉 [主控] 代码审查通过！项目顺利结项！")
            return current_code
        else:
            print(f"❌ [主控] 代码被打回，Review 意见: {feedback}")
            print(f"   (将打回意见通过【消息传递协议】发送回 Coder 信箱...)")
            
    print("\n⚠️ [主控] 达到最大轮次 3，项目流产！CTO 介入烂尾楼。")
    return current_code


if __name__ == "__main__":
    task = "写一个 Python 函数，接收一个列表，如果列表中有重复元素就返回 True，否则返回 False。但注意：绝对不能使用 set()，而且时间复杂度要低于 O(N^2)"
    final_code = run_multi_agent_company(task)
    print("\n🚀 最终上线的代码:\n")
    print(final_code)
