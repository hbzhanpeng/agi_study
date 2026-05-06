# config.py
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'week4', '.env'))

API_KEY = os.getenv("SILICONFLOW_API_KEY")
# 本地微调模型服务地址
# LLM_BASE_URL = "http://localhost:8001/v1"
LLM_BASE_URL = "https://api.siliconflow.cn/v1"
# 向量模型（通常还是用云端，除非本地也部署了向量模型服务器）
EMBED_BASE_URL = "https://api.siliconflow.cn/v1"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
EMBED_MODEL = "BAAI/bge-large-zh-v1.5"
CHAT_MODEL = "Qwen/Qwen2.5-7B-Instruct"