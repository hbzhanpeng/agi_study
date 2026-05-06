# mcp_server.py - 提供文件操作工具
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
import asyncio

app = Server("file-server")

@app.list_tools()
async def list_tools():
    """告诉Client我有哪些工具"""
    return [
        types.Tool(
            name="read_file",
            description="读取本地文件内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"}
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="write_file",
            description="写入内容到本地文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "要写入的内容"}
                },
                "required": ["path", "content"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """执行工具"""
    if name == "read_file":
        with open(arguments["path"], "r", encoding="utf-8") as f:
            content = f.read()
        return [types.TextContent(type="text", text=content)]
    
    elif name == "write_file":
        with open(arguments["path"], "w", encoding="utf-8") as f:
            f.write(arguments["content"])
        return [types.TextContent(type="text", text=f"文件已写入：{arguments['path']}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())