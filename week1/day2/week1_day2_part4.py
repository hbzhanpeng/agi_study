# ============================================================
# 第 1 周 Day 2 - Part 4：综合实战
# ============================================================
#
# 目标：用闭包 + 装饰器 + 生成器写一个「迷你 LLM API 调用框架」
# 这就是你以后做 AI 项目的日常代码风格
# ============================================================

import time
import random
import json
from functools import wraps


# ============================================================
# 4.1 工具集：用装饰器构建可复用的工具
# ============================================================


# ---- 装饰器 1：计时 + 日志 ----
def log_and_time(func):
    """记录函数调用日志和耗时"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        print(f"[CALL] {func.__name__} 开始")
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            print(f"[DONE] {func.__name__} 完成 ({elapsed:.3f}s)")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            print(f"[FAIL] {func.__name__} 失败 ({elapsed:.3f}s): {e}")
            raise

    return wrapper


# ---- 装饰器 2：带参数的重试（闭包 + 装饰器结合）----
def retry(max_attempts=3, delay=0.05, exceptions=(Exception,)):
    """
    生产级重试装饰器
    - max_attempts: 最大重试次数
    - delay: 重试间隔（秒）
    - exceptions: 需要重试的异常类型元组
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts:
                        print(
                            f"  [RETRY {attempt}/{max_attempts}] {func.__name__}: {e}"
                        )
                        time.sleep(delay)
                    else:
                        print(
                            f"  [GIVE UP] {func.__name__}: 重试 {max_attempts} 次后仍失败"
                        )
            raise last_error

        return wrapper

    return decorator


# ---- 装饰器 3：缓存（闭包实现 memoize）----
def cache(func):
    """用闭包实现的函数结果缓存"""
    _cache = {}  # 闭包变量
    hit_count = [0]  # 用列表绕过 nonlocal（另一种技巧）
    miss_count = [0]

    @wraps(func)
    def wrapper(*args):
        key = args
        if key in _cache:
            hit_count[0] += 1
            return _cache[key]
        miss_count[0] += 1
        result = func(*args)
        _cache[key] = result
        return result

    # 在 wrapper 上挂额外方法（装饰器进阶技巧）
    wrapper.cache_info = lambda: {
        "hits": hit_count[0],
        "misses": miss_count[0],
        "size": len(_cache),
    }
    wrapper.cache_clear = lambda: _cache.clear()
    return wrapper


# ============================================================
# 4.2 模拟 LLM API：用生成器实现流式输出
# ============================================================


class FakeLLM:
    """模拟大模型 API —— 展示闭包+装饰器+生成器的综合运用"""

    def __init__(self, model_name="fake-gpt-4"):
        self.model_name = model_name
        self._call_count = 0

    @log_and_time
    @retry(max_attempts=3, delay=0.02, exceptions=(ConnectionError,))
    def chat(self, prompt: str) -> str:
        """非流式调用（一次性返回）"""
        self._call_count += 1

        # 模拟 20% 失败率
        if random.random() < 0.2:
            raise ConnectionError("模拟网络超时")

        # 模拟推理延迟
        time.sleep(0.01)
        return f"[{self.model_name}] 关于'{prompt}'的回答：AGI 是通用人工智能的缩写。"

    def stream_chat(self, prompt: str):
        """
        流式调用（生成器逐 token 返回）

        这就是 OpenAI 的 stream=True 的简化版
        真实场景中每个 yield 会通过 SSE 推送到前端
        """
        response = f"关于'{prompt}'：AGI 即通用人工智能，是 AI 发展的终极目标。它能像人类一样处理任何智能任务。"

        # 逐字符输出（真实场景是逐 token）
        for i, char in enumerate(response):
            time.sleep(0.005)  # 模拟推理延迟
            yield {
                "id": f"chunk-{i}",
                "model": self.model_name,
                "choices": [
                    {"delta": {"content": char}, "index": 0, "finish_reason": None}
                ],
            }

        # 发送结束信号
        yield {
            "id": f"chunk-{len(response)}",
            "model": self.model_name,
            "choices": [{"delta": {}, "index": 0, "finish_reason": "stop"}],
        }


# ============================================================
# 4.3 用缓存装饰器优化 Embedding 计算
# ============================================================


@cache
@log_and_time
def get_embedding(text: str) -> list:
    """
    模拟 Embedding 计算

    真实场景：调用 OpenAI 的 text-embedding-ada-002
    相同文本的 embedding 不会变，所以必须缓存
    """
    time.sleep(0.01)
    # 模拟返回一个 384 维向量
    return [random.random() for _ in range(8)]  # 简化为 8 维


# ============================================================
# 4.4 生成器管道：处理对话历史
# ============================================================


def generate_chat_history():
    """生成器：模拟从数据库逐条读取对话记录"""
    history = [
        {"role": "user", "content": "什么是 AGI？", "timestamp": 1000},
        {"role": "assistant", "content": "AGI 是通用人工智能", "timestamp": 1001},
        {"role": "user", "content": "它和 AI 有什么区别？", "timestamp": 1002},
        {
            "role": "assistant",
            "content": "AI 是窄域的，AGI 是通用的",
            "timestamp": 1003,
        },
        {"role": "system", "content": "你是一个 AI 助手", "timestamp": 999},
        {"role": "user", "content": "谢谢", "timestamp": 1004},
    ]
    for msg in history:
        yield msg


def filter_by_role(messages, roles):
    """生成器管道：按角色过滤消息"""
    for msg in messages:
        if msg["role"] in roles:
            yield msg


def format_for_prompt(messages):
    """生成器管道：格式化为 prompt 格式"""
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        yield f"<{role}>{content}</{role}>"


def limit_tokens(messages, max_messages=3):
    """生成器管道：限制消息数量（模拟 token 窗口）"""
    count = 0
    for msg in messages:
        if count >= max_messages:
            return  # 在生成器中 return 等于结束迭代
        yield msg
        count += 1


# ============================================================
# 运行演示
# ============================================================

if __name__ == "__main__":
    random.seed(42)  # 固定随机数，方便复现

    # ---- 演示 1：非流式调用（装饰器叠加）----
    print("=" * 60)
    print("演示 1：非流式调用（自动重试 + 计时日志）")
    print("=" * 60)

    llm = FakeLLM("fake-gpt-4")
    try:
        result = llm.chat("什么是 AGI")
        print(f"结果: {result}")
    except ConnectionError:
        print("最终调用失败")

    # ---- 演示 2：流式调用（生成器）----
    print(f"\n{'=' * 60}")
    print("演示 2：流式调用（打字机效果）")
    print("=" * 60)

    print("AI: ", end="", flush=True)
    for chunk in llm.stream_chat("什么是 AGI"):
        content = chunk["choices"][0]["delta"].get("content", "")
        print(content, end="", flush=True)
    print()  # 换行

    # ---- 演示 3：缓存装饰器 ----
    print(f"\n{'=' * 60}")
    print("演示 3：Embedding 缓存")
    print("=" * 60)

    # 第一次：计算
    emb1 = get_embedding("什么是 AGI")
    # 第二次：命中缓存（不会重新计算）
    emb2 = get_embedding("什么是 AGI")
    # 第三次：新文本，重新计算
    emb3 = get_embedding("什么是 LLM")

    print(f"\n缓存统计: {get_embedding.cache_info()}")
    print(f"emb1 == emb2? {emb1 == emb2}")  # True

    # ---- 演示 4：生成器管道 ----
    print(f"\n{'=' * 60}")
    print("演示 4：生成器管道处理对话历史")
    print("=" * 60)

    # 管道组装：读取 → 过滤(只要user和assistant) → 限制数量 → 格式化
    pipeline = format_for_prompt(
        limit_tokens(
            filter_by_role(generate_chat_history(), roles=["user", "assistant"]),
            max_messages=3,
        )
    )

    print("构造的 Prompt：")
    for line in pipeline:
        print(f"  {line}")

    print(f"\n[OK] Day 2 综合实战 完成")
