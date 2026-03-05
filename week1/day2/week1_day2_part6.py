# ============================================================
# 第 1 周 Day 2 - Part 6：避坑指南（面试高频陷阱）
# ============================================================

from functools import wraps


# ============================================================
# 坑 1：装饰器吃掉了异常栈（生产环境最常踩）
# ============================================================

print("--- 坑 1：装饰器吞异常 ---")


# 错误写法：catch 了异常但只 print，不 raise
def bad_error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"  出错了: {e}")  # 吞掉了异常！调用方不知道失败了
            return None  # 静默返回 None

    return wrapper


@bad_error_handler
def divide(a, b):
    return a / b


result = divide(1, 0)
print(f"  result = {result}")  # None，调用方以为成功了！
print(f"  type = {type(result)}")  # NoneType


# 正确写法：记录日志后 re-raise，或者明确返回错误
def good_error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"  [ERROR] {func.__name__}: {e}")
            raise  # 关键！把异常抛回给调用方

    return wrapper


@good_error_handler
def divide_v2(a, b):
    return a / b


try:
    divide_v2(1, 0)
except ZeroDivisionError:
    print("  调用方正确捕获了异常")

# 【面试要点】AI 项目中，调 LLM API 如果装饰器吞了异常，
# 你会以为模型返回了 None，实际上是网络超时。排查起来非常痛苦。


# ============================================================
# 坑 2：生成器的「一次性消费」问题
# ============================================================

print(f"\n--- 坑 2：生成器只能遍历一次 ---")


def get_numbers():
    yield from range(5)


gen = get_numbers()

# 第一次：正常
total = sum(gen)
print(f"  第一次 sum = {total}")  # 10

# 第二次：空了！
total2 = sum(gen)
print(f"  第二次 sum = {total2}")  # 0 ← 生成器已耗尽

# 【踩坑场景】AI 项目中处理 Embedding 结果时：
# embeddings = model.encode(texts)  ← 如果返回的是生成器
# 你第一次遍历存了数据库，第二次想打印验证就是空的

# 解决方案 1：需要多次使用时，先转成列表
nums_list = list(get_numbers())
print(f"  转列表后：sum1={sum(nums_list)}, sum2={sum(nums_list)}")


# 解决方案 2：用函数而不是变量（每次调用创建新生成器）
def get_nums():
    return get_numbers()  # 每次调用都返回新的生成器


print(f"  函数方式：sum1={sum(get_nums())}, sum2={sum(get_nums())}")


# ============================================================
# 坑 3：装饰器在类方法上的 self 问题
# ============================================================

print(f"\n--- 坑 3：装饰器 + 类方法的 self ---")

# 错误理解：很多人以为 *args 会自动处理 self
# 实际上 *args 确实会处理，但如果装饰器里要用参数位置就容易搞混


def validate_positive(func):
    """校验第一个数值参数为正数"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # 坑：对于类方法，args[0] 是 self，args[1] 才是真正的参数！
        # 如果你写 if args[0] <= 0，那就是在拿 self 和 0 比较
        return func(*args, **kwargs)

    return wrapper


# 正确做法：用 **kwargs 或者明确知道参数位置
def validate_input(param_name):
    """通过参数名校验（更安全的写法）"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import inspect

            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            value = bound.arguments.get(param_name)
            if value is not None and value <= 0:
                raise ValueError(f"{param_name} 必须为正数，收到: {value}")
            return func(*args, **kwargs)

        return wrapper

    return decorator


class Model:
    @validate_input("temperature")
    def generate(self, prompt: str, temperature: float = 0.7):
        return f"Generated with temp={temperature}"


model = Model()
print(f"  正常调用: {model.generate('hello', temperature=0.5)}")
try:
    model.generate("hello", temperature=-0.1)
except ValueError as e:
    print(f"  校验拦截: {e}")


# ============================================================
# 坑 4（额外赠送）：闭包变量的延迟绑定 + 类属性的坑
# ============================================================

print(f"\n--- 坑 4：闭包变量延迟绑定（再强调） ---")

# 这个坑太常见了，再用一个 AI 场景的例子
# 场景：批量创建不同 temperature 的模型配置

configs = {}
for temp in [0.1, 0.5, 0.9]:
    configs[f"temp_{temp}"] = lambda: {"temperature": temp}

# 你以为：
# configs["temp_0.1"]() → {"temperature": 0.1}
# 实际：
print("  错误版本（全是 0.9）：")
for name, fn in configs.items():
    print(f"    {name}: {fn()}")  # 全是 0.9！

# 正确写法
configs_fixed = {}
for temp in [0.1, 0.5, 0.9]:
    configs_fixed[f"temp_{temp}"] = lambda t=temp: {"temperature": t}

print("  正确版本（各不相同）：")
for name, fn in configs_fixed.items():
    print(f"    {name}: {fn()}")


print(f"\n[OK] Part 6 避坑指南 完成")
