import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
from typing import List, Dict, Tuple

def evaluate_and_convert(dialogues: List[Dict]) -> Tuple[List[Dict], Dict]:
    """
    评估数据质量并转换为 ShareGPT 格式
    
    参数:
        dialogues: 原始对话列表，格式 [{"user": "...", "assistant": "..."}, ...]
    
    返回:
        sharegpt_data: ShareGPT 格式的对话列表
        quality_report: 质量报告 {
            "total": 总数,
            "empty_user": 空用户输入数,
            "empty_assistant": 空助手回复数,
            "valid": 有效对话数,
            "avg_user_length": 平均用户输入长度,
            "avg_assistant_length": 平均助手回复长度
        }
    """
    # TODO: 实现评估和转换逻辑
    # 提示：
    # 1. 遍历对话，统计空值
    # 2. 过滤掉有空值的对话
    # 3. 计算长度统计
    # 4. 转换为 ShareGPT 格式: {"conversations": [{"from": "human", "value": "..."}, {"from": "gpt", "value": "..."}]}
    total = len(dialogues)
    empty_user_count = 0
    empty_assistant_count = 0
    
    # 1. 过滤有效对话
    valid_dialogues = []
    for dialogue in dialogues:
        user = dialogue.get("user", "").strip()
        assistant = dialogue.get("assistant", "").strip()
        
        # 统计空值
        if not user:
            empty_user_count += 1
        if not assistant:
            empty_assistant_count += 1
        
        # 只保留两者都非空的对话
        if user and assistant:
            valid_dialogues.append(dialogue)
    
    # 2. 计算有效对话的平均长度
    if valid_dialogues:
        avg_user_length = sum(len(d["user"]) for d in valid_dialogues) / len(valid_dialogues)
        avg_assistant_length = sum(len(d["assistant"]) for d in valid_dialogues) / len(valid_dialogues)
    else:
        avg_user_length = 0
        avg_assistant_length = 0
    
    # 3. 转换为 ShareGPT 格式
    sharegpt_data = []
    for dialogue in valid_dialogues:
        sharegpt_data.append({
            "conversations": [
                {"from": "human", "value": dialogue["user"]},
                {"from": "gpt", "value": dialogue["assistant"]}
            ]
        })
    
    # 4. 返回结果（注意这里返回 sharegpt_data，不是空列表）
    return sharegpt_data, {
        "total": total,
        "empty_user": empty_user_count,  # 数量，不是比率
        "empty_assistant": empty_assistant_count,  # 数量，不是比率
        "valid": len(valid_dialogues),  # 有效对话数
        "avg_user_length": avg_user_length,
        "avg_assistant_length": avg_assistant_length
    }

# 测试代码
if __name__ == "__main__":
    raw_dialogues = [
        {
            "user": "你好，我想咨询一下退货流程",
            "assistant": "您好！退货流程很简单：1. 登录账号 2. 进入订单页面 3. 点击退货按钮"
        },
        {
            "user": "",  # 空用户输入
            "assistant": "有什么可以帮助您的吗？"
        },
        {
            "user": "产品质量很好",
            "assistant": "感谢您的认可！"
        },
        {
            "user": "物流速度怎么样？",
            "assistant": ""  # 空助手回复
        },
    ]
    
    sharegpt_data, quality_report = evaluate_and_convert(raw_dialogues)
    
    print("=== 数据质量报告 ===")
    for key, value in quality_report.items():
        if "avg" in key:
            print(f"{key}: {value:.1f}")
        else:
            print(f"{key}: {value}")
    
    print("\n=== ShareGPT 格式数据 ===")
    for i, dialogue in enumerate(sharegpt_data, 1):
        print(f"\n对话 {i}:")
        print(json.dumps(dialogue, ensure_ascii=False, indent=2))
