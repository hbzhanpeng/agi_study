# ============================================================
# 第 1 周 Day 2 - Part 2：装饰器（Decorator）
# ============================================================
#
# 前端类比：
# - 装饰器 ≈ React 的 HOC（高阶组件）
# - 用一个函数"包裹"另一个函数，增强它的功能
# - JS 也有装饰器语法（TC39 Stage 3），用法几乎一样
#
# 理解路径：高阶函数 → 闭包 → 装饰器（装饰器本质就是闭包的语法糖）
# ============================================================

import time
from functools import wraps


# ============================================================
# 2.1 装饰器的本质：它不是什么魔法，就是高阶函数
# ============================================================

# 第一步：理解高阶函数（函数作为参数 + 返回函数）
# ≈ JS: const withLog = (fn) => (...args) => { console.log('call'); return fn(...args); }


def simple_log(func):
    """最简单的装饰器：在函数执行前后打印日志"""

    def wrapper(*args, **kwargs):
        print(f"  [LOG] 调用 {func.__name__}，参数: args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"  [LOG] {func.__name__} 返回: {result}")
        return result

    return wrapper


# 不用 @ 语法的写法（帮你理解本质）
def add(a, b):
    return a + b


print("--- 2.1 装饰器本质 ---")
print("原始调用：", add(1, 2))

add_with_log = simple_log(add)  # 手动装饰
print("装饰后调用：")
add_with_log(1, 2)


# ============================================================
# 2.2 @ 语法糖 —— 上面的简写
# ============================================================

# @simple_log 等价于 multiply = simple_log(multiply)


@simple_log
def multiply(a, b):
    """两数相乘"""
    return a * b


print("\n--- 2.2 @ 语法糖 ---")
multiply(3, 4)

# 【面试考点】装饰后函数的 __name__ 变了！
print(f"\nmultiply.__name__ = {multiply.__name__}")  # wrapper，不是 multiply！
print(f"multiply.__doc__  = {multiply.__doc__}")  # None，不是 "两数相乘"！
# 这就是为什么需要 @wraps


# ============================================================
# 2.3 @wraps —— 保留原函数信息（面试必问）
# ============================================================


def better_log(func):
    """使用 @wraps 保留原函数元信息"""

    @wraps(func)  # ← 关键！保留 __name__, __doc__, __module__ 等
    def wrapper(*args, **kwargs):
        print(f"  [LOG] 调用 {func.__name__}")
        return func(*args, **kwargs)

    return wrapper


@better_log
def divide(a, b):
    """安全除法"""
    return a / b if b != 0 else None


print("\n--- 2.3 @wraps ---")
divide(10, 3)
print(f"divide.__name__ = {divide.__name__}")  # divide（正确了！）
print(f"divide.__doc__  = {divide.__doc__}")  # 安全除法（正确了！）


# ============================================================
# 2.4 实用装饰器：计时器（AI 开发中高频使用）
# ============================================================


def timer(func):
    """测量函数执行时间 —— AI 项目中调模型、跑推理时必备"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  [{func.__name__}] 耗时: {elapsed:.4f}s")
        return result

    return wrapper


@timer
def slow_function():
    """模拟一个耗时操作"""
    total = sum(i * i for i in range(1_000_000))
    return total


print("\n--- 2.4 计时器装饰器 ---")
result = slow_function()
print(f"  结果: {result}")


# ============================================================
# 2.5 带参数的装饰器（面试进阶，三层嵌套）
# ============================================================

# 需求：重试 N 次（AI 调用外部 API 时经常需要）
#
# 理解方式：
# @retry(max_retries=3) 实际上是：
# 1. retry(max_retries=3) 先执行，返回一个装饰器 decorator
# 2. decorator(func) 再执行，返回 wrapper
# 所以是 三层嵌套：参数层 → 装饰器层 → 包裹层


def retry(max_retries=3, delay=0.1):
    """带参数的重试装饰器 —— 调 LLM API 必备"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    print(f"  [RETRY] {func.__name__} 第 {attempt} 次失败: {e}")
                    if attempt < max_retries:
                        time.sleep(delay)
            raise last_exception

        return wrapper

    return decorator


# 模拟一个不稳定的 API 调用
call_count = 0


@retry(max_retries=3, delay=0.01)
def unstable_api_call():
    """模拟不稳定的外部 API"""
    global call_count
    call_count += 1
    if call_count < 3:
        raise ConnectionError(f"网络超时 (第{call_count}次)")
    return {"status": "success", "data": "AI response"}


print("\n--- 2.5 带参数的装饰器（重试） ---")
try:
    result = unstable_api_call()
    print(f"  最终成功: {result}")
except ConnectionError as e:
    print(f"  最终失败: {e}")


# ============================================================
# 2.6 多个装饰器叠加（执行顺序 —— 面试必考！）
# ============================================================


def decorator_a(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("  A 前")
        result = func(*args, **kwargs)
        print("  A 后")
        return result

    return wrapper


def decorator_b(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("  B 前")
        result = func(*args, **kwargs)
        print("  B 后")
        return result

    return wrapper


@decorator_a
@decorator_b
def say_hello():
    print("  Hello!")


print("\n--- 2.6 多装饰器执行顺序 ---")
print("@decorator_a  @decorator_b  def say_hello")
print("等价于: say_hello = decorator_a(decorator_b(say_hello))")
print("执行顺序: A前 → B前 → Hello → B后 → A后")
print()
say_hello()
# 输出顺序：A前 → B前 → Hello! → B后 → A后
# 【记忆口诀】装饰从下往上包，执行从外往内跑


# ============================================================
# 2.7 类装饰器（了解即可，面试偶尔问）
# ============================================================


class CallCounter:
    """用类实现装饰器 —— 通过 __call__ 魔术方法"""

    def __init__(self, func):
        self.func = func
        self.count = 0
        wraps(func)(self)  # 保留原函数信息

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"  [{self.func.__name__}] 被调用了 {self.count} 次")
        return self.func(*args, **kwargs)


@CallCounter
def greet(name):
    return f"Hello, {name}!"


print("\n--- 2.7 类装饰器 ---")
print(greet("Alice"))
print(greet("Bob"))
print(greet("Charlie"))
print(f"总调用次数: {greet.count}")


print("\n[OK] Part 2 装饰器 完成")
