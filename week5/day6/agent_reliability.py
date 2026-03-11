import time
import random

# ===== 模拟工具库 =====
AVAILABLE_TOOLS = {
    "get_order": {"params": ["order_id"]},
    "send_email": {"params": ["to", "subject", "body"]},
    "query_policy": {"params": ["policy_type"]},
}


def mock_tool_execute(tool_name: str, args: dict) -> dict:
    """模拟工具执行（随机失败模拟网络问题）"""
    if random.random() < 0.4:  # 40% 概率失败
        raise TimeoutError("工具调用超时")
    return {"status": "success", "data": f"{tool_name} 执行结果"}


# ===== 你需要实现的部分 =====


def validate_tool_call(tool_name: str, args: dict) -> tuple[bool, str]:
    """
    TODO 1: 实现工具调用校验
    需要检查：
    1. tool_name 是否在 AVAILABLE_TOOLS 中
    2. args 中的参数是否包含该工具所需的所有 params

    返回：(是否合法, 错误信息)
    合法时返回 (True, "OK")
    不合法时返回 (False, "具体错误原因")
    """
    if tool_name not in AVAILABLE_TOOLS:
        return False, "工具不存在"
    
    required_params = AVAILABLE_TOOLS[tool_name]["params"]
    for param in required_params:
        if param not in args:
            return False, f"参数缺失: {param}"
    return True, "OK"
    


def execute_with_retry(tool_name: str, args: dict, max_retries: int = 3) -> dict:
    """
    TODO 2: 实现带重试的工具执行
    需要：
    1. 先调用 validate_tool_call 校验
    2. 校验失败直接返回错误，不重试
    3. 执行失败（TimeoutError）时指数退避重试
    4. 超过 max_retries 次后返回失败结果

    返回格式：{"success": bool, "data": ..., "error": ...}
    """
    is_valid, error_msg = validate_tool_call(tool_name, args)
    if not is_valid:
        return {"success": False, "error": error_msg}
    
    for attempt in range(max_retries):
        try:
            result = mock_tool_execute(tool_name, args)
            return {"success": True, "data": result}
        except TimeoutError:
            if attempt < max_retries - 1:
                print(f"工具调用失败，正在重试第 {attempt + 1} 次...")
                time.sleep(2 ** attempt)
                continue
            else:
                return {"success": False, "error": "工具调用失败，已达最大重试次数"}


# ===== 测试代码（不要修改）=====
if __name__ == "__main__":
    print("=== 测试 1：合法调用 ===")
    result = execute_with_retry("get_order", {"order_id": "#12345"})
    print(result)

    print("\n=== 测试 2：工具不存在 ===")
    result = execute_with_retry("delete_all_data", {"confirm": True})
    print(result)

    print("\n=== 测试 3：参数缺失 ===")
    result = execute_with_retry("send_email", {"to": "user@example.com"})
    print(result)
