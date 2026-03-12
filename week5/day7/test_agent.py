"""
测试自主 Agent
"""

from autonomous_agent import AutonomousAgent


def test_basic():
    agent = AutonomousAgent(api_key="your-api-key")

    # 测试 1: 搜索功能
    result = agent.search_web("Python 最新版本")
    print(f"搜索结果: {result}")

    # 测试 2: 文件读写
    agent.write_file("test.txt", "Hello Agent")
    content = agent.read_file("test.txt")
    print(f"文件内容: {content}")

    # 测试 3: 代码生成
    result = agent.generate_code("计算斐波那契数列", "python", "fibonacci.py")
    print(f"代码生成: {result}")


if __name__ == "__main__":
    test_basic()
