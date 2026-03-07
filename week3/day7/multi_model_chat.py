"""
Week 3 Day 7 实战：支持多模型切换的智能对话系统
目标：用适配器模式实现统一 LLM 接口，支持一行切换模型
"""
import json
import random
import sys
import io
# Windows 终端默认 GBK 编码，中文子词 token 可能解码失败，强制 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ========== 基类：统一的 LLM 接口 ==========
class BaseLLM:
    """所有模型适配器的基类，定义统一接口"""
    
    def __init__(self, model_name):
        self.model_name = model_name
    
    def chat(self, messages, temperature=0.7, max_tokens=500):
        """统一的对话接口，子类必须实现"""
        raise NotImplementedError("子类必须实现 chat 方法")


# ========== TODO 1: 实现 OpenAI 适配器 ==========
# 继承 BaseLLM，实现 chat 方法
# 因为没有真实 API Key，用 mock 返回即可
class OpenAILLM(BaseLLM):
    def __init__(self):
        super().__init__("gpt-4")
    
    def chat(self, messages, temperature=0.7, max_tokens=500):
        # TODO: 返回一个模拟的回复
        # 格式：f"[{self.model_name}] 收到消息: {最后一条用户消息的内容}"
        return f"[{self.model_name}] 收到消息：{messages[-1]["content"]}"


# ========== TODO 2: 实现通义千问适配器 ==========
class QwenLLM(BaseLLM):
    def __init__(self):
        super().__init__("qwen-turbo")
    
    def chat(self, messages, temperature=0.7, max_tokens=500):
        # TODO: 同样返回模拟回复
        return f"[{self.model_name}] 收到消息：{messages[-1]["content"]}"


# ========== TODO 3: 实现 DeepSeek 适配器 ==========
class DeepSeekLLM(BaseLLM):
    def __init__(self):
        super().__init__("deepseek-chat")
    
    def chat(self, messages, temperature=0.7, max_tokens=500):
        # TODO: 同样返回模拟回复
        return f"[{self.model_name}] 收到消息：{messages[-1]["content"]}"


# ========== TODO 4: 实现工厂函数 ==========
# 根据模型名称返回对应的 LLM 实例
def get_llm(model_name):
    # TODO: 用字典映射模型名称到类
    # "openai" → OpenAILLM()
    # "qwen" → QwenLLM()
    # "deepseek" → DeepSeekLLM()
    # 如果名称不存在，抛出 ValueError
    model_map = {
        "openai": OpenAILLM(),
        "qwen": QwenLLM(),
        "deepseek": DeepSeekLLM()
    }
    if model_name not in model_map:
        raise ValueError(f"不支持的模型: {model_name}")
    return model_map[model_name]


# ========== TODO 5: 实现 fallback 机制 ==========
# 主模型失败时自动切换到备用模型
def chat_with_fallback(messages, primary="openai", backup="qwen"):
    # TODO: 
    # 1. 先尝试用 primary 模型
    # 2. 如果出错（try/except），自动切到 backup 模型
    # 3. 打印出 "主模型失败，切换到备用模型" 的提示
    try:
        llm = get_llm(primary)
        return llm.chat(messages)
    except Exception as e:
        print(f"主模型失败，切换到备用模型")
        llm = get_llm(backup)
        return llm.chat(messages)


# ========== 测试代码（不需要修改） ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🧪 测试 1: 基本对话")
    print("=" * 50)
    
    messages = [
        {"role": "system", "content": "你是一个 AI 助手"},
        {"role": "user", "content": "你好，请介绍一下 RAG 系统"}
    ]
    
    # 测试三个模型
    for model_name in ["openai", "qwen", "deepseek"]:
        llm = get_llm(model_name)
        response = llm.chat(messages)
        print(f"  {response}")
    
    print("\n" + "=" * 50)
    print("🧪 测试 2: 一行切换模型")
    print("=" * 50)
    
    # 展示一行切换的便利性
    model = "deepseek"
    llm = get_llm(model)
    print(f"  当前使用: {llm.model_name}")
    print(f"  {llm.chat(messages)}")
    
    print("\n" + "=" * 50)
    print("🧪 测试 3: Fallback 机制")
    print("=" * 50)
    
    # 测试正常情况
    result = chat_with_fallback(messages, primary="openai", backup="qwen")
    print(f"  正常: {result}")
    
    # 测试主模型失败（用不存在的模型名）
    result = chat_with_fallback(messages, primary="不存在的模型", backup="deepseek")
    print(f"  降级: {result}")
    
    print("\n✅ 所有测试通过！")
