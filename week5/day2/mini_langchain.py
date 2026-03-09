"""
Week 5 Day 2 实战：手写 Mini-LangChain
目标：从零实现 LangChain 的 5 大核心组件，理解框架内部设计
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'week4', '.env'))
API_KEY = os.getenv("SILICONFLOW_API_KEY")
BASE_URL = "https://api.siliconflow.cn/v1"


# ============================================================
# 组件 1: BaseLLM（LLM 基类）
# ============================================================
# 前端类比：axios 实例（封装 API 调用细节）
class BaseLLM:
    def __init__(self, model="deepseek-ai/DeepSeek-V2.5", temperature=0):
        self.model = model
        self.temperature = temperature
        self.callbacks = []  # 回调钩子列表
    
    def add_callback(self, callback):
        self.callbacks.append(callback)
    
    def call(self, prompt):
        # 触发回调：LLM 开始
        for cb in self.callbacks:
            cb.on_llm_start(prompt)
        
        resp = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": 500
            },
            timeout=30
        )
        result = resp.json()["choices"][0]["message"]["content"].strip()
        
        # 触发回调：LLM 结束
        for cb in self.callbacks:
            cb.on_llm_end(result)
        
        return result


# ============================================================
# 组件 2: PromptTemplate（提示词模板）
# ============================================================
# 前端类比：模板字符串 / React 组件 props
class PromptTemplate:
    def __init__(self, template, input_variables):
        self.template = template
        self.input_variables = input_variables
    
    def format(self, **kwargs):
        """把变量填入模板"""
        return self.template.format(**kwargs)


# ============================================================
# 组件 3: Chain（链式调用）
# ============================================================
# 前端类比：Promise.then().then() 或 pipe 管道

class LLMChain:
    """最基础的 Chain：Prompt → LLM → 输出"""
    def __init__(self, llm, prompt):
        self.llm = llm
        self.prompt = prompt
    
    def run(self, **kwargs):
        formatted = self.prompt.format(**kwargs)
        return self.llm.call(formatted)


class SequentialChain:
    """顺序链：把多个 Chain 串联，上一个的输出是下一个的输入"""
    def __init__(self, chains):
        self.chains = chains
    
    def run(self, initial_input):
        result = initial_input
        for i, chain in enumerate(self.chains):
            print(f"  🔗 Chain {i+1}: 执行中...")
            result = chain.run(text=result)
            print(f"  ✅ 输出: {result[:50]}...")
        return result


# ============================================================
# TODO 1: 实现 Tool（工具注册）
# ============================================================
# 前端类比：Express 路由注册
class Tool:
    """
    工具类：封装一个可被 Agent 调用的功能
    
    TODO: 实现 __init__ 和 run 方法
    属性：
    - name: 工具名称（如 "calculator"）
    - description: 工具描述（LLM 靠这个选工具！）
    - func: 实际执行的函数
    
    提示：
    def __init__(self, name, description, func):
        # 保存三个属性
    
    def run(self, input):
        # 调用 self.func(input) 并返回结果
    """
    def __init__(self, name, description, func):
        self.name = name
        self.description = description
        self.func = func
    
    def run(self, input):
        return self.func(input)


# ============================================================
# TODO 2: 实现 Memory（对话记忆）
# ============================================================
# 前端类比：Redux store + localStorage

class ConversationBufferMemory:
    """
    缓冲记忆：保存完整对话历史
    
    TODO: 实现 add_message 和 get_history 方法
    属性：
    - messages: 列表，保存所有对话 [{"role": "user", "content": "..."}, ...]
    
    提示：
    def __init__(self):
        self.messages = []
    
    def add_message(self, role, content):
        # 把 {"role": role, "content": content} 加入 messages
    
    def get_history(self):
        # 返回所有消息拼成的字符串
    """
    def __init__(self):
        self.messages = []

    def add_message(self, role,content):
        self.messages.append({"role": role, "content": content})

    def get_history(self):
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.messages])


class ConversationSummaryMemory:
    """
    摘要记忆：用 LLM 压缩对话历史
    
    TODO: 实现 add_message 和 get_history 方法
    属性：
    - llm: 用于生成摘要的 LLM
    - summary: 当前对话摘要字符串
    - message_count: 消息计数
    
    提示：
    def __init__(self, llm):
        self.llm = llm
        self.summary = ""
        self.message_count = 0
    
    def add_message(self, role, content):
        self.message_count += 1
        # 每 3 条消息用 LLM 压缩一次摘要
        if self.message_count % 3 == 0:
            compress_prompt = f"请用一句话总结以下对话：\n当前摘要：{self.summary}\n新消息：{role}: {content}"
            self.summary = self.llm.call(compress_prompt)
        else:
            self.summary += f"\n{role}: {content}"
    
    def get_history(self):
        return self.summary
    """
    def __init__(self, llm):
        self.llm = llm
        self.summary = ""
        self.message_count = 0
    
    def add_message(self, role, content):
        self.message_count += 1
        if self.message_count % 3 == 0:
            compress_prompt = f"请用一句话总结以下对话：\n当前摘要：{self.summary}\n新消息：{role}: {content}"
            self.summary = self.llm.call(compress_prompt)
        else:
            self.summary += f"\n{role}: {content}"
    
    def get_history(self):
        return self.summary


# ============================================================
# 组件 5: Callback（回调钩子）
# ============================================================
# 前端类比：React useEffect / Vue watch

class LogCallback:
    """日志回调：记录每次 LLM 调用"""
    def on_llm_start(self, prompt):
        print(f"  📤 [LOG] LLM 输入: {prompt[:60]}...")
    
    def on_llm_end(self, result):
        print(f"  📥 [LOG] LLM 输出: {result[:60]}...")


class TokenCountCallback:
    """Token 计费回调"""
    def __init__(self):
        self.total_chars = 0
    
    def on_llm_start(self, prompt):
        self.total_chars += len(prompt)
    
    def on_llm_end(self, result):
        self.total_chars += len(result)
        print(f"  💰 [TOKEN] 累计字符: {self.total_chars}")


# ============================================================
# LCEL 风格管道（Bonus）
# ============================================================
class Pipeline:
    """
    LCEL 管道：用 | 运算符串联组件
    前端类比：Unix 管道 cat file | grep | sort
    """
    def __init__(self, func):
        self.func = func
    
    def __or__(self, other):
        """重载 | 运算符"""
        def combined(input):
            return other.func(self.func(input))
        return Pipeline(combined)
    
    def invoke(self, input):
        return self.func(input)


# ============================================================
# 测试（不需要修改）
# ============================================================
if __name__ == "__main__":
    llm = BaseLLM()
    
    # --- 测试 1: Chain ---
    print("=" * 60)
    print("🧪 测试 1: LLMChain（单链）")
    print("=" * 60)
    
    translate_prompt = PromptTemplate(
        template="请把以下中文翻译成英文，只返回翻译结果：\n{text}",
        input_variables=["text"]
    )
    translate_chain = LLMChain(llm=llm, prompt=translate_prompt)
    result = translate_chain.run(text="人工智能正在改变世界")
    print(f"翻译结果: {result}")
    
    # --- 测试 2: SequentialChain ---
    print("\n" + "=" * 60)
    print("🧪 测试 2: SequentialChain（顺序链）")
    print("=" * 60)
    
    summarize_prompt = PromptTemplate(
        template="请用一句话总结以下内容：\n{text}",
        input_variables=["text"]
    )
    chain1 = LLMChain(llm=llm, prompt=translate_prompt)
    chain2 = LLMChain(llm=llm, prompt=summarize_prompt)
    seq_chain = SequentialChain([chain1, chain2])
    result = seq_chain.run("公司每年提供5000元培训基金，员工可自主选择外部培训课程")
    print(f"最终结果: {result}")
    
    # --- 测试 3: Tool ---
    print("\n" + "=" * 60)
    print("🧪 测试 3: Tool（工具注册）")
    print("=" * 60)
    
    calc_tool = Tool(
        name="calculator",
        description="计算数学表达式",
        func=lambda expr: str(eval(expr))
    )
    print(f"工具名: {calc_tool.name}")
    print(f"工具描述: {calc_tool.description}")
    print(f"调用结果: {calc_tool.run('100 * 0.8')}")
    
    # --- 测试 4: Memory ---
    print("\n" + "=" * 60)
    print("🧪 测试 4: Memory（对话记忆）")
    print("=" * 60)
    
    memory = ConversationBufferMemory()
    memory.add_message("user", "你好，我叫小明")
    memory.add_message("assistant", "你好小明！")
    memory.add_message("user", "我的名字是什么？")
    print(f"Buffer 记忆:\n{memory.get_history()}")
    
    print("\n--- Summary Memory ---")
    summary_mem = ConversationSummaryMemory(llm=llm)
    summary_mem.add_message("user", "你好，我叫小明，我入职3年了")
    summary_mem.add_message("assistant", "你好小明，入职3年享有15天年假")
    summary_mem.add_message("user", "培训基金有多少？")
    print(f"Summary 记忆:\n{summary_mem.get_history()}")
    
    # --- 测试 5: Callback ---
    print("\n" + "=" * 60)
    print("🧪 测试 5: Callback（回调钩子）")
    print("=" * 60)
    
    llm_with_cb = BaseLLM()
    llm_with_cb.add_callback(LogCallback())
    llm_with_cb.add_callback(TokenCountCallback())
    llm_with_cb.call("用一句话解释什么是 AI Agent")
    
    # --- 测试 6: LCEL 管道 ---
    print("\n" + "=" * 60)
    print("🧪 测试 6: LCEL 管道语法")
    print("=" * 60)
    
    upper = Pipeline(lambda x: x.upper())
    add_emoji = Pipeline(lambda x: f"🤖 {x}")
    add_end = Pipeline(lambda x: f"{x} !!!")
    
    pipe = upper | add_emoji | add_end
    result = pipe.invoke("hello langchain")
    print(f"管道结果: {result}")
