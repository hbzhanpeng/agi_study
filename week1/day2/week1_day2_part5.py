# ============================================================
# 第 1 周 Day 2 - Part 5：面试手写题
# ============================================================

import time
from functools import wraps
from collections import deque


# ============================================================
# 面试题 8：手写限流装饰器（滑动窗口算法）
# ============================================================
#
# 这道题综合考察：
# 1. 三层嵌套的带参装饰器（闭包）
# 2. 滑动窗口算法（deque 数据结构）
# 3. @wraps 的使用
# 4. 异常设计
#
# AI 场景：调用 OpenAI API 有速率限制（RPM），需要客户端限流


class RateLimitExceeded(Exception):
    """自定义异常 —— 面试加分：不用通用 Exception"""

    pass


def rate_limit(calls=5, period=60):
    """
    滑动窗口限流装饰器

    Args:
        calls: period 时间窗口内允许的最大调用次数
        period: 时间窗口大小（秒）

    原理（对标前端）：
    ≈ 前端的 throttle，但更精确
    用一个队列记录每次调用的时间戳，
    每次调用前清理过期时间戳，检查队列长度
    """

    def decorator(func):
        # 闭包变量：滑动窗口（用 deque 存储调用时间戳）
        call_times = deque()

        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()

            # 清理过期的调用记录（滑出窗口的）
            while call_times and call_times[0] <= now - period:
                call_times.popleft()

            # 检查是否超过限制
            if len(call_times) >= calls:
                wait_time = call_times[0] + period - now
                raise RateLimitExceeded(
                    f"{func.__name__} 调用频率超限！"
                    f"({calls}次/{period}秒)，请等待 {wait_time:.1f}s"
                )

            # 记录本次调用时间并执行
            call_times.append(now)
            return func(*args, **kwargs)

        # 挂载辅助方法（方便调试）
        wrapper.reset = lambda: call_times.clear()
        wrapper.remaining = lambda: calls - len(call_times)

        return wrapper

    return decorator


# 测试限流装饰器
@rate_limit(calls=3, period=1)  # 每秒最多 3 次
def call_api(prompt):
    return f"Response to: {prompt}"


print("--- 面试题 8：限流装饰器测试 ---")
for i in range(5):
    try:
        result = call_api(f"prompt_{i}")
        print(f"  [{i}] 成功: {result} (剩余: {call_api.remaining()})")
    except RateLimitExceeded as e:
        print(f"  [{i}] 被限流: {e}")

# 等待窗口过期后重试
print("  等待 1.1 秒...")
time.sleep(1.1)
result = call_api("after_wait")
print(f"  等待后成功: {result}")


# ============================================================
# 面试题 9：闭包 + 生成器综合 —— 实现协程调度器
# ============================================================
#
# 这道题展示生成器作为"穷人的协程"的用法
# Python 3.5 之前没有 async/await，生成器就是协程
# 面试中展示这个理解 = 深度加分


def task_scheduler():
    """
    用生成器模拟简单的任务调度器

    原理：每个 task 是一个生成器，
    调度器轮流给每个 task 执行一步（yield 暂停）
    ≈ JS 的事件循环 + 微任务队列的简化版
    """
    tasks = []  # 任务队列

    def add_task(gen):
        """添加一个生成器任务"""
        tasks.append(gen)

    def run():
        """轮询执行所有任务（Round-Robin 调度）"""
        while tasks:
            # 取出队首任务
            task = tasks.pop(0)
            try:
                # 执行到下一个 yield
                result = next(task)
                print(f"    任务产出: {result}")
                # 没结束就放回队尾
                tasks.append(task)
            except StopIteration:
                print(f"    一个任务完成了")

    return add_task, run


def download_task(name, steps=3):
    """模拟下载任务（每个 yield 代表下载一部分）"""
    for i in range(steps):
        yield f"{name}: 下载进度 {(i + 1) * 100 // steps}%"


print(f"\n--- 面试题 9：生成器任务调度器 ---")
add_task, run = task_scheduler()
add_task(download_task("文件A", 3))
add_task(download_task("文件B", 2))
add_task(download_task("文件C", 4))
print("  开始调度（Round-Robin）：")
run()


# ============================================================
# 面试题 10：装饰器 + 类型检查（运行时类型校验）
# ============================================================
#
# Python 的类型标注不强制，但面试可能让你写一个运行时校验的装饰器
# 这在 AI 项目中很实用：确保传给模型的数据类型正确


def type_check(func):
    """
    运行时类型检查装饰器
    根据函数的类型标注，在运行时校验参数类型

    ≈ 给 Python 加上 TypeScript 的运行时校验
    """
    import inspect

    @wraps(func)
    def wrapper(*args, **kwargs):
        # 获取函数签名
        sig = inspect.signature(func)
        # 获取类型标注
        hints = func.__annotations__

        # 绑定实际参数到形参
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        # 逐个检查类型
        for param_name, value in bound.arguments.items():
            if param_name in hints and param_name != "return":
                expected_type = hints[param_name]
                if not isinstance(value, expected_type):
                    raise TypeError(
                        f"参数 '{param_name}' 期望 {expected_type.__name__}，"
                        f"实际收到 {type(value).__name__}: {value!r}"
                    )

        # 执行原函数
        result = func(*args, **kwargs)

        # 检查返回值类型
        if "return" in hints:
            expected = hints["return"]
            if not isinstance(result, expected):
                raise TypeError(
                    f"返回值期望 {expected.__name__}，"
                    f"实际是 {type(result).__name__}: {result!r}"
                )

        return result

    return wrapper


@type_check
def create_prompt(system: str, user: str, temperature: float = 0.7) -> str:
    return f"[system]{system}[user]{user}[temp={temperature}]"


print(f"\n--- 面试题 10：运行时类型检查 ---")

# 正确调用
result = create_prompt("你是AI助手", "什么是AGI？", 0.5)
print(f"  正确调用: {result}")

# 错误调用：temperature 传了字符串
try:
    create_prompt("你是AI助手", "什么是AGI？", "high")
except TypeError as e:
    print(f"  类型错误被拦截: {e}")

# 错误调用：user 传了整数
try:
    create_prompt("你是AI助手", 12345)
except TypeError as e:
    print(f"  类型错误被拦截: {e}")


print(f"\n[OK] Part 5 面试手写题 完成")
