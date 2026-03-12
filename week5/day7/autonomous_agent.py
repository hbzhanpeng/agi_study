"""
Week 5 Day 7: 自主 Agent 实战
功能：网络搜索 + 文件操作 + 代码生成
"""

import os
import json
import requests
from typing import List, Dict, Any


class AutonomousAgent:
    """自主 Agent - 支持工具调用"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.conversation_history = []
        self.tools = self._define_tools()

    def _define_tools(self) -> List[Dict[str, Any]]:
        """定义 Agent 可用的工具"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "搜索网络获取实时信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "搜索关键词"}
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "读取本地文件内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "文件路径"}
                        },
                        "required": ["file_path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "写入内容到文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "文件路径"},
                            "content": {"type": "string", "description": "文件内容"},
                        },
                        "required": ["file_path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_code",
                    "description": "生成代码并保存到文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "代码功能描述",
                            },
                            "language": {
                                "type": "string",
                                "description": "编程语言",
                                "enum": ["python", "javascript", "java"],
                            },
                            "file_path": {"type": "string", "description": "保存路径"},
                        },
                        "required": ["description", "language", "file_path"],
                    },
                },
            },
        ]
        self.tools = self._define_tools()

    def _call_llm(self, messages: List[Dict]) -> Dict:
        """调用 LLM API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": self.tools,
            "tool_choice": "auto",
        }
        response = requests.post(self.api_url, headers=headers, json=payload)
        return response.json()

    # TODO: 实现工具函数
    def search_web(self, query: str) -> str:
        """搜索网络 - 你来实现"""
        # 提示：可以使用 DuckDuckGo 或模拟搜索结果
        return f"模拟搜索结果: {query}"

    def read_file(self, file_path: str) -> str:
        """读取文件 - 你来实现"""
        return ""

    def write_file(self, file_path: str, content: str) -> str:
        """写入文件 - 你来实现"""
        return "success"

    def generate_code(self, description: str, language: str, file_path: str) -> str:
        """生成代码 - 你来实现"""
        # 提示：调用 LLM 生成代码，然后保存
        return "success"

    def _execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """执行工具调用"""
        if tool_name == "search_web":
            return self.search_web(arguments["query"])
        elif tool_name == "read_file":
            return self.read_file(arguments["file_path"])
        elif tool_name == "write_file":
            return self.write_file(arguments["file_path"], arguments["content"])
        elif tool_name == "generate_code":
            return self.generate_code(
                arguments["description"], arguments["language"], arguments["file_path"]
            )
        return "Unknown tool"

    def run(self, user_input: str, max_iterations: int = 5) -> str:
        """运行 Agent - ReAct 循环"""
        self.conversation_history.append({"role": "user", "content": user_input})

        for i in range(max_iterations):
            response = self._call_llm(self.conversation_history)
            message = response["choices"][0]["message"]

            if message.get("tool_calls"):
                self.conversation_history.append(message)

                for tool_call in message["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    arguments = json.loads(tool_call["function"]["arguments"])
                    result = self._execute_tool(tool_name, arguments)

                    self.conversation_history.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": result,
                        }
                    )
            else:
                return message["content"]

        return "达到最大迭代次数"
