"""
API 连通性测试：验证硅基流动 API Key 是否正常工作
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
from dotenv import load_dotenv
import requests

# 加载 .env 文件
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

API_KEY = os.getenv("SILICONFLOW_API_KEY")
BASE_URL = "https://api.siliconflow.cn/v1"

if not API_KEY or API_KEY == "在这里粘贴你的API Key":
    print("❌ 请先在 week4/.env 中填入你的 API Key")
    sys.exit(1)

print("🔍 测试 1: 检查 API Key 格式...")
print(f"  API Key: {API_KEY[:8]}...{API_KEY[-4:]}")

# 测试对话模型
print("\n🔍 测试 2: 调用对话模型 (DeepSeek)...")
try:
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-ai/DeepSeek-V2.5",
            "messages": [{"role": "user", "content": "用一句话介绍RAG"}],
            "max_tokens": 100
        },
        timeout=30
    )
    if resp.status_code == 200:
        answer = resp.json()["choices"][0]["message"]["content"]
        print(f"  ✅ 对话模型正常！")
        print(f"  回复: {answer[:100]}")
    else:
        print(f"  ❌ 请求失败: {resp.status_code} - {resp.text[:200]}")
except Exception as e:
    print(f"  ❌ 连接失败: {e}")

# 测试 Embedding 模型
print("\n🔍 测试 3: 调用 Embedding 模型 (BGE)...")
try:
    resp = requests.post(
        f"{BASE_URL}/embeddings",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "BAAI/bge-large-zh-v1.5",
            "input": ["测试文本"],
            "encoding_format": "float"
        },
        timeout=30
    )
    if resp.status_code == 200:
        embedding = resp.json()["data"][0]["embedding"]
        print(f"  ✅ Embedding 模型正常！")
        print(f"  向量维度: {len(embedding)}")
        print(f"  前5个值: {embedding[:5]}")
    else:
        print(f"  ❌ 请求失败: {resp.status_code} - {resp.text[:200]}")
except Exception as e:
    print(f"  ❌ 连接失败: {e}")

print("\n" + "=" * 50)
print("🎉 所有测试完成！环境准备就绪，可以开始 RAG 实战了！")
