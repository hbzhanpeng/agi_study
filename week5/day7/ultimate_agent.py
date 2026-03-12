"""
Week 5 Day 7 终极挑战：构建《自主防御型全栈 Agent》
目标：
1. 实现 ReAct (Thought-Action-Observation) 核心循环
2. 实现多分支工具路由
3. 实现自愈(Auto-healing)与人类审批(HITL)防线
"""
import os
import json
import subprocess
import requests
import sys
import time
from dotenv import load_dotenv

# 环境初始化
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'week4', '.env'))
API_KEY = os.getenv("SILICONFLOW_API_KEY")
BASE_URL = "https://api.siliconflow.cn/v1"

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================
# 🛠️ 模块 1：工具箱 (The Sandbox Tools)
# ============================================================

def search_web(query):
    """模拟联网搜索"""
    print(f"  [🌐 搜索中...] 查询关键字: {query}")
    knowledge_base = {
        "Python 3.12 新特性": "Python 3.12 引入了更强大的 match-case 语法，支持更复杂的子模式匹配。以及改进了 f-string 的解析机制。",
        "match-case 语法示例": "match x: case (a, b): print(f'Point {a},{b}'); case _: print('Other')"
    }
    for key in knowledge_base:
        if any(word in key for word in query.split()):
            return knowledge_base[key]
    return "没有找到相关的互联网搜索结果。"

def save_file_with_hitl(filename, content):
    """TODO: 实现人类介入(HITL)审批后再保存文件"""
    print(f"\n🚨 [HITL 权限拦截] 智能体申请写入文件: {filename}")
    
    # TODO: 获取用户输入 yes/no
    # 如果 yes，则执行写文件并返回成功信息；如果 no，返回拒绝信息。
    confirm = input("是否写入文件？(yes/no)")
    if confirm == "yes":
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ 文件 {filename} 已成功写入。"
    else:
        return f"❌ 文件 {filename} 写入被拒绝。"
    

def run_python_code_sandbox(code_content):
    """
    TODO: 在沙盒中运行 Python 代码并捕获报错 (Error-to-Insight)
    """
    print("  [🧪 沙盒执行] 正在尝试运行生成的 Python 代码...")
    temp_file = "temp_sandbox.py"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(code_content)
    
    try:
        # 使用 sys.executable 替代 "python" 以确保跨平台兼容性
        result = subprocess.run([sys.executable, temp_file], capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            return result.stdout
        else:
            return f"❌ 运行错误：{result.stderr}"
    except Exception as e:
        return f"❌ 系统错误：{str(e)}"
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)


# ============================================================
# 🧠 模块 2：自主大脑 (The ReAct Pipeline)
# ============================================================

class UltimateAgent:
    def __init__(self, model="deepseek-ai/DeepSeek-V2.5"):
        self.model = model
        self.memory = [
            {"role": "system", "content": """
            你是一个具备安全防护能力的自主智能体。
            任务处理流程：Thought (思考建议) -> Action (JSON格式调用工具) -> Observation (观察结果) -> 反思及修复。
            可用工具格式: 
            1. {"action": "search_web", "params": {"query": "..."}}
            2. {"action": "save_file_with_hitl", "params": {"filename": "...", "content": "..."}}
            3. {"action": "run_python_code_sandbox", "params": {"code_content": "..."}}
            当任务完成，输出 Final Answer。
            """}
        ]

    def call_llm(self, retries=3):
        for i in range(retries):
            try:
                resp = requests.post(
                    f"{BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                    json={"model": self.model, "messages": self.memory, "temperature": 0},
                    timeout=60
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                if i < retries - 1:
                    wait_time = 2 ** i  # 指数退避：1s, 2s, 4s...
                    print(f"  [⚠️ API 连接重试] {e}，正在 {wait_time}s 后进行第 {i+1} 次重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e

    def run(self, user_prompt, max_turns=8):
        """
        TODO 核心挑战：实现 ReAct 推理回环
        """
        self.memory.append({"role": "user", "content": user_prompt})
        
        for i in range(max_turns):
            print(f"\n🌀 --- 第 {i+1} 轮推理 ---")
            
            # TODO 1: 调用 LLM 获取当前思考和行动
            # TODO 2: 解析返回文本，如果是 Final Answer 则结束
            # TODO 3: 如果是调用工具，提取 JSON 并根据 action 分发给对应的工具函数
            # TODO 4: 将工具返回的 Observation 塞回 memory，继续下一轮循环
            
            llm_response = self.call_llm()
            self.memory.append({"role": "assistant", "content": llm_response})
            
            if "Final Answer" in llm_response:
                return llm_response
            
            # 鲁棒的 JSON 解析
            try:
                import re
                # 兼容 ```json ... ``` 也兼容直接输出的 JSON
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    action_json = json.loads(json_match.group())
                    action = action_json["action"]
                    params = action_json["params"]
                    
                    if action == "search_web":
                        observation = search_web(params.get("query", ""))
                    elif action == "save_file_with_hitl":
                        observation = save_file_with_hitl(params.get("filename", "output.txt"), params.get("content", ""))
                    elif action == "run_python_code_sandbox":
                        observation = run_python_code_sandbox(params.get("code_content", ""))
                    else:
                        observation = f"❌ 未知工具: {action}"
                else:
                    observation = "❌ 未在回复中检测到标准的 Action JSON 指令"
                
                print(f"👁️ Observation: {observation[:150]}...")
                self.memory.append({"role": "user", "content": f"Observation: {observation}"})
                
            except Exception as e:
                observation = f"❌ 执行指令时报错: {str(e)}"
                self.memory.append({"role": "user", "content": f"Observation: {observation}"})
            

        return "已达到最大推理步数。"

if __name__ == "__main__":
    agent = UltimateAgent()
    # 终极任务：搜索特性 -> 存文件 -> 写演示代码 -> 运行(并根据可能的报错自动纠错)
    mission = "搜索 Python 3.12 特性，保存为 py312.md，并写一段 match-case 演示代码运行（故意包含一个小语法错误，看你能否根据报错自动修正它）"
    
    print(agent.run(mission))
