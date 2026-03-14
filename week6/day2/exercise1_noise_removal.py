import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import re
from typing import List

def clean_noise(text: str) -> str:
    """
    数据去噪函数
    
    要求：
    1. 移除 HTML 标签（如 <p>, <div>, <span> 等）
    2. 移除 URL（支持 http 和 https）
    3. 移除多余的空格和换行符（连续空格变成单个空格）
    4. 移除首尾空格
    
    返回清洗后的文本
    """
    # TODO: 在这里实现你的代码
    # 提示：使用 re.sub() 函数
    #1. 移除 html 标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 2. 移除 URL
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # 3. 移除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

# 测试用例
test_cases = [
    "<div>产品很好用！</div>",
    "访问 https://example.com 了解更多   ",
    "<p>客服态度   不错</p>  推荐",
    "正常文本  没有  噪声",
]

# 运行测试
if __name__ == "__main__":
    for text in test_cases:
        cleaned = clean_noise(text)
        print(f"原始: {text}")
        print(f"清洗: {cleaned}")
        print("---")
