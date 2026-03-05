import json
# 导入常用的类型提示 (Python 3.9+ 之后，很多基础类型可以直接用内置的 list/dict，但 typing 模块依然不可或缺)
from typing import List, Dict, Union, Optional, Any
# 1. 基础类型提示 (Type Hints) ======================
# 这就像 TS 里的 function processUser(name: string, age: number, isVip: boolean = false): string
def process_user(name: str, age: int, is_vip: bool = False) -> str:
    status = "VIP" if is_vip else "Normal"
    return f"User {name} (Age {age}) is {status}"
# 2. 复合类型提示 (List, Dict, Optional) ======================
# Optional[str] 表示这个值要么是字符串，要么是 None (相当于 TS 里的 string | null)
# List[Dict[str, Any]] 表示一个列表，里面装的是字典，字典的键是字符串，值是任意类型 (Any)
def fetch_ai_history(user_id: int) -> Optional[List[Dict[str, Any]]]:
    # 模拟从数据库或 API 获取的数据
    if user_id <= 0:
        return None  # 如果 ID 不合法，返回 None
    
    return [
        {"role": "user", "content": "你好", "tokens": 2},
        {"role": "assistant", "content": "你好！我是 AGI 导师。", "tokens": 10, "is_safe": True}
    ]
# 3. JSON 处理 ======================
print("--- JSON 操作演示 ---")
# Python 字典对象
user_data: Dict[str, Any] = {
    "name": "Alex",
    "skills": ["Python", "React", "Prompt"],
    "is_active": True,
    "score": None
}
# 相当于 JS 的 JSON.stringify()：将 Python 对象转成 JSON 字符串
# indent=2 用来美化输出，ensure_ascii=False 保证中文正常显示
json_str: str = json.dumps(user_data, indent=2, ensure_ascii=False)
print(f"转为 JSON 字符串:\n{json_str}")
# 相当于 JS 的 JSON.parse()：将 JSON 字符串转回 Python 对象 (通常是字典或列表)
parsed_data: Dict[str, Any] = json.loads(json_str)
print(f"解析回 Python 字典: {parsed_data['skills'][0]}")



def parse_llm_response(response_str: str) -> Dict[str, Any]:
    try:
        json_data = json.loads(response_str)
        return json_data
    except json.JSONDecodeError:
        return {}

parse_llm_response('{"status": "success", "answer": "The capital of France is Paris."}')