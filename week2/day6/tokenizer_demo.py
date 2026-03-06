"""
Day 6 实操：Tokenizer 分词体验
目标：亲手感受 BPE 分词器如何处理中英文文本
"""
import sys
import io
# Windows 终端默认 GBK 编码，中文子词 token 可能解码失败，强制 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import tiktoken

# ========== TODO 1: 加载 tokenizer ==========
# 提示：用 tiktoken.get_encoding() 方法
# GPT-4 的编码名称是 "cl100k_base"
enc = tiktoken.get_encoding("cl100k_base")


# ========== TODO 2: 准备文本并编码 ==========
english_text = "Hello, how are you?"
chinese_text = "你好，你怎么样？"

# 提示：用 enc.encode(text) 方法把文本转成 token ID 列表
en_tokens = enc.encode(english_text)
cn_tokens = enc.encode(chinese_text)

# ========== TODO 3: 打印 token 数量 ==========
# 提示：len() 可以获取列表长度
print(f"英文 Token 数量: {len(en_tokens)}")
print(f"中文 Token 数量: {len(cn_tokens)}")

# ========== TODO 4: 逐个解码，看看每个 token 对应什么 ==========
# 提示：用 for 循环遍历 token 列表
#       用 enc.decode([single_id]) 把单个 token ID 解码回文本
print("\n英文逐个解码:")
# 在这里写 for 循环...
for tik in en_tokens:
    print(enc.decode([tik]))

print("\n中文逐个解码:")
# 在这里写 for 循环...
for tik in cn_tokens:
    print(enc.decode([tik]))

# ========== TODO 5: 思考并写注释 ==========
# 为什么中文的 token 数量比英文多？
# 你的答案：中文转成字节码占用的多一些
