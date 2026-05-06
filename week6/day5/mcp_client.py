# mcp_client.py - 连接MCP Server，让Agent使用工具
import asyncio
import json
import requests
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from config import API_KEY, LLM_BASE_URL, CHAT_MODEL

async def run():
    # 1. 启动MCP Server子进程，建立连接
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 2. 初始化
            await session.initialize()
            
            # 3. 获取Server提供的工具列表
            tools_result = await session.list_tools()
            print("Server提供的工具：")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # 4. 把MCP工具转成LLM能认识的tools格式
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                }
                for tool in tools_result.tools
            ]
            
            # 5. 调用LLM
            user_input = "帮我读取train.json文件的内容"
            messages = [
                {"role": "system", "content": "你是一个文件助手，可以读写本地文件。"},
                {"role": "user", "content": user_input}
            ]
            
            resp = requests.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": CHAT_MODEL,
                    "messages": messages,
                    "temperature": 0,
                    "max_tokens": 500,
                    "tools": tools
                },
                timeout=120
            )
            message = resp.json()["choices"][0]["message"]
            
            # 6. 如果LLM要调用工具
            if message.get("tool_calls"):
                tool_call = message["tool_calls"][0]
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                print(f"\n调用工具: {tool_name}，参数: {tool_args}")
                
                # 7. 通过MCP Session执行工具（不是自己执行！）
                result = await session.call_tool(tool_name, tool_args)
                print(f"工具返回: {result.content[0].text[:200]}")
            else:
                print(f"LLM直接回答: {message['content']}")

if __name__ == "__main__":
    asyncio.run(run())