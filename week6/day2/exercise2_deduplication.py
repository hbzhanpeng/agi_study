import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import hashlib
from typing import List, Tuple, Dict

def jaccard_similarity(text1: str, text2: str, threshold: float = 0.85) -> float:
    """计算两个字符串的 Jaccard 相似度"""
    # 将文本转换为字符集合
    set1 = set(text1)
    set2 = set(text2)
    
    # 计算 Jaccard 相似度
    intersection = len(set1 & set2)  # 交集
    union = len(set1 | set2)          # 并集
    
    if union == 0:
        return False
    
    similarity = intersection / union
    
    return similarity >= threshold

def dedup_pipeline(texts: List[str], threshold: float = 0.85) -> Tuple[List[str], Dict]:
    """
    完整的去重流水线
    
    参数:
        texts: 原始文本列表
        threshold: 模糊去重的相似度阈值
    
    返回:
        deduplicated: 去重后的文本列表
        stats: 统计信息 {"original": 原始数量, "exact_removed": 精确去重数, "fuzzy_removed": 模糊去重数, "final": 最终数量}
    """
    # TODO: 实现去重逻辑
    # 提示：
    # 1. 先用 set 存储已见过的哈希值，做精确去重
    # 2. 再对剩余文本做两两比对，计算 Jaccard 相似度
    # 3. 记录每个阶段去除的数量
    seen_hashes = set()
    exact_removed = 0
    fuzzy_removed = 0
    final_removed = 0
    
    # 1. 精确去重
    deduplicated = []
    for text in texts:
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        if text_hash not in seen_hashes:
            seen_hashes.add(text_hash)
            deduplicated.append(text)
        else:
            exact_removed += 1
    
    # 2. 模糊去重
    # 2. 模糊去重（正确做法）
    final_result = []
    for text in deduplicated:  # 遍历精确去重后的列表
        is_duplicate = False
        
        # 检查当前文本是否与已保留的文本相似
        for kept_text in final_result:
            if jaccard_similarity(text, kept_text, threshold):
                is_duplicate = True
                fuzzy_removed += 1
                break
        
        # 如果不重复，加入最终结果
        if not is_duplicate:
            final_result.append(text)
    return final_result, {
        "original": len(texts),
        "exact_removed": exact_removed,
        "fuzzy_removed": fuzzy_removed,
        "final": len(final_result)
    }

# 测试代码
if __name__ == "__main__":
    comments = [
        "产品质量很好，物流也快！",
        "产品质量很好，物流也快！",
        "产品质量很好,物流也快!",
        "产品质量很好，物流也快！！！",
        "客服态度不错，推荐购买",
        "客服态度不错，推荐购买。",
        "价格有点贵",
    ]
    
    result, stats = dedup_pipeline(comments)
    
    print("=== 去重统计 ===")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n=== 去重结果 ===")
    for i, text in enumerate(result, 1):
        print(f"{i}. {text}")
