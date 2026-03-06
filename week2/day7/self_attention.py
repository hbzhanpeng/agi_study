"""
Day 7 实操：手写 Self-Attention
目标：用 NumPy 实现 Attention(Q, K, V) = softmax(Q × K^T / √d_k) × V
"""
import numpy as np
import sys
import io
# Windows 终端默认 GBK 编码，中文子词 token 可能解码失败，强制 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

np.random.seed(42)

# 模拟输入：3 个词，每个词 4 维向量
# 可以理解为一个句子有 3 个 token，每个 token 的 embedding 是 4 维
X = np.random.randn(3, 4)
print("输入 X (3个词 × 4维):")
print(X)

# 权重矩阵（实际中这些是可训练参数，训练时会不断更新）
d_k = 4
W_Q = np.random.randn(4, d_k)
W_K = np.random.randn(4, d_k)
W_V = np.random.randn(4, d_k)

# ========== TODO 1: 计算 Q, K, V ==========
# 提示：矩阵乘法用 np.dot() 或 @ 运算符
# Q = X × W_Q,  K = X × W_K,  V = X × W_V
Q = np.dot(X, W_Q)
K = np.dot(X, W_K)
V = np.dot(X, W_V)

# ========== TODO 2: 计算注意力分数 ==========
# 公式：scores = Q × K^T / √d_k
# 提示：转置用 K.T，开方用 np.sqrt()
scores = np.dot(Q, K.T) / np.sqrt(d_k)  

# ========== TODO 3: softmax 归一化 ==========
# 提示：softmax(x) = exp(x) / sum(exp(x))
# 对每一行做 softmax（axis=1），用 keepdims=True 保持维度
def softmax(x):
    return np.exp(x) / np.sum(np.exp(x), axis=1, keepdims=True)

attention_weights = softmax(scores)

# ========== TODO 4: 加权求和得到输出 ==========
# 公式：output = attention_weights × V
output = attention_weights @ V

# ========== 打印结果 ==========
print("\n注意力权重（每行加起来=1）:")
print(attention_weights)
print("\n验证每行之和:", attention_weights.sum(axis=1))
print("\n输出 (3个词 × 4维):")
print(output)
