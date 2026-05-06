import numpy as np
import sys
import io

# Windows 控制台 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

def self_attention(Q, K, V):
    d_k = Q.shape[-1]
    # 你来写：计算注意力分数，返回加权后的值
    scores = Q @ K.T / np.sqrt(d_k)
    weights = softmax(scores)
    return weights @ V

# 假设有3个词，每个词是4维向量
np.random.seed(42)
Q = np.random.randn(3, 4)  # 3个词的Query
K = np.random.randn(3, 4)  # 3个词的Key
V = np.random.randn(3, 4)  # 3个词的Value

output = self_attention(Q, K, V)
print("输入shape:", Q.shape)
print("输出shape:", output.shape)
print("输出:\n", output)


def multi_head_attention(Q, K, V, num_heads=2):
    d_k = Q.shape[-1] // num_heads  # 每个 head 的维度
    
    # 把 Q、K、V 拆成 num_heads 份
    # 每份独立做 self_attention
    # 最后拼接起来
    
    heads = []
    for i in range(num_heads):
        # 你来写：取第 i 个 head 的 Q、K、V 片段，做 self_attention
        q_i = Q[:, i * d_k : (i + 1) * d_k]
        k_i = K[:, i * d_k : (i + 1) * d_k]
        v_i = V[:, i * d_k : (i + 1) * d_k]
        heads.append(self_attention(q_i, k_i, v_i))
    
    return np.concatenate(heads, axis=-1)
np.random.seed(42)
Q = np.random.randn(3, 4)
K = np.random.randn(3, 4)
V = np.random.randn(3, 4)

output = multi_head_attention(Q, K, V, num_heads=2)
print("输入shape:", Q.shape)
print("输出shape:", output.shape)

def length_of_longest_substring(s: str) -> int:
    """
    寻找无重复字符的最长子串的长度
    """
    char_index_map = {}
    max_len = 0
    start = 0
    
    for i, char in enumerate(s):
        # 如果字符出现过，且其索引在当前窗口内，则移动窗口左边界
        if char in char_index_map and char_index_map[char] >= start:
            start = char_index_map[char] + 1
            
        # 更新字符的最新索引
        char_index_map[char] = i
        # 更新最大长度
        max_len = max(max_len, i - start + 1)
        
    return max_len

print(length_of_longest_substring("abcabcbb"))  # 期望 3
print(length_of_longest_substring("bbbbb"))      # 期望 1
print(length_of_longest_substring("pwwkew"))     # 期望 3