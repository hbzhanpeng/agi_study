import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class AgentMemoryManager:
    def __init__(self, window_size=3):
        # 长期记忆：记录真实的对话历史
        self.long_term_memory = []
        # 短期记忆：记录当前任务的执行草稿/中间过程
        self.working_memory = []
        # 滑动窗口大小（保留最近 N 轮问答，即 N*2 条消息）
        self.window_size = window_size
        
    def add_user_message(self, content):
        """用户发来新消息时，加进长期记忆，同时【必须清空】上一次的短期工作记忆！"""
        self.long_term_memory.append({"role": "user", "content": content})
        self.working_memory.clear()  # === 注意这个细节！====
        
    def add_final_answer(self, content):
        """Agent计算完给出最终答复时，加进长期记忆"""
        self.long_term_memory.append({"role": "assistant", "content": content})
        
    def add_tool_scratchpad(self, tool_name, tool_result):
        """记录工具调用的中间临时结果（只进临时短期记忆！）"""
        self.working_memory.append({
            "role": "function", 
            "name": tool_name, 
            "content": f"执行结果: {tool_result}"
        })
        
    def get_prompt_messages(self):
        """
        🚀 面试核心考点 / TODO 区域！
        拼装发给大模型的 messages 数组。顺序非常重要！
        
        拼装规则：
        1. 首先，如果长期记忆太长了，只截取最近的 window_size 轮对话（一问一答算1轮，最新这句用户话算一轮的一部分）。
        2. 然后，把当前还在进行中的短期工作记忆 (working_memory) 拼在最后面。
        3. 返回完整的合并后的 list。
        """
        messages = []
        
        # ==========================================
        # TODO: 请你补全截取长期记忆和拼接短期记忆的代码！
        # ==========================================
        current_long_term_memory = self.long_term_memory[-(self.window_size * 2 + 1):]
        messages.extend(current_long_term_memory)
        messages.extend(self.working_memory)
        
        return messages

# 测试用例 (请确保输出符合预期)
if __name__ == "__main__":
    mem = AgentMemoryManager(window_size=2)
    
    # 历史乱聊 (最早的)
    mem.add_user_message("你好")
    mem.add_final_answer("你好！")
    mem.add_user_message("今天天气不错")
    mem.add_final_answer("是的。")
    
    # 当前对话
    mem.add_user_message("我叫小明，帮我查查我的年假有多少天？")
    mem.add_tool_scratchpad("lookup", "发现员工：小明 - 年假 15天") # 调了数据库
    mem.add_tool_scratchpad("calculator", "15 - 0 = 15")     # 算了一下
    
    # 获取准备发给 LLM 的 messages
    msgs = mem.get_prompt_messages()
    
    import json
    print(json.dumps(msgs, ensure_ascii=False, indent=2))
    print(f"\n一共应该只有 {(2 * 2) + 1 + 2} 条消息才对！(2轮完成对话*2 + 当前用户1条 + 2条工作记忆)")
