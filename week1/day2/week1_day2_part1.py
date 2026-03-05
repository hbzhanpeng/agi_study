# ============================================================
# 第 1 周 Day 2 - Part 1：闭包（Closure）
# ============================================================
#
# 前端类比：Python 闭包和 JS 闭包几乎一模一样
# JS 闭包: function outer() { let x = 0; return function() { x++; return x; } }
# Py 闭包: 一样的逻辑，语法不同
# ============================================================


# ---- 1.1 什么是闭包？----
# 闭包 = 函数 + 它引用的外部变量
# 条件：① 嵌套函数 ② 内部函数引用外部变量 ③ 外部函数返回内部函数


def make_counter():
    """创建一个计数器 —— 经典闭包示例"""
    count = 0  # 自由变量（free variable），被内部函数捕获

    def counter():
        nonlocal count  # 关键！声明要修改外部变量（≈ JS 天然支持）
        count += 1
        return count

    return counter  # 返回函数本身，不是调用结果


# 使用
c1 = make_counter()
c2 = make_counter()  # 独立的闭包实例

print("--- 闭包基础 ---")
print(f"c1(): {c1()}")  # 1
print(f"c1(): {c1()}")  # 2
print(f"c1(): {c1()}")  # 3
print(f"c2(): {c2()}")  # 1 ← c2 是独立的，不影响 c1


# ---- 1.2 nonlocal vs global ----
# 【面试考点】这是 Python 闭包和 JS 闭包最大的区别！

# JS 中：内部函数可以直接修改外部变量
# Python：读取外部变量没问题，但要 **修改** 必须用 nonlocal

x = 100  # 全局变量


def outer():
    x = 10  # 外部函数的局部变量

    def inner_read():
        print(f"  读取外部 x = {x}")  # OK，直接读

    def inner_modify():
        nonlocal x  # 没有这行就会报错 UnboundLocalError
        x += 1
        print(f"  修改后 x = {x}")

    def inner_global():
        global x  # 修改的是全局的 x，不是 outer 的 x
        x += 1
        print(f"  全局 x = {x}")

    inner_read()
    inner_modify()
    inner_global()
    print(f"  outer 的 x = {x}")


print("\n--- nonlocal vs global ---")
outer()
print(f"全局 x = {x}")  # 101


# ---- 1.3 闭包的实际应用 ----


# 应用 1：配置工厂（≈ JS 的高阶函数 / React 的 HOC）
def make_multiplier(factor):
    """创建一个乘法器"""

    def multiply(x):
        return x * factor

    return multiply


double = make_multiplier(2)
triple = make_multiplier(3)
print(f"\n--- 闭包应用：配置工厂 ---")
print(f"double(5) = {double(5)}")  # 10
print(f"triple(5) = {triple(5)}")  # 15


# 应用 2：缓存/记忆化（≈ React 的 useMemo）
def make_cache():
    """简单的缓存闭包"""
    cache = {}

    def cached_func(key, compute_fn):
        if key not in cache:
            print(f"  计算 {key}...")
            cache[key] = compute_fn()
        else:
            print(f"  命中缓存 {key}")
        return cache[key]

    return cached_func


print(f"\n--- 闭包应用：缓存 ---")
get_or_compute = make_cache()
get_or_compute("a", lambda: 1 + 1)  # 计算
get_or_compute("a", lambda: 1 + 1)  # 命中缓存
get_or_compute("b", lambda: 2 + 2)  # 计算


# ---- 1.4 闭包经典陷阱（面试常考！）----

# 【坑】循环中的闭包 —— JS 和 Python 都有这个问题
# JS 中用 var 会踩坑，用 let 解决
# Python 中：

print(f"\n--- 闭包陷阱 ---")

# 错误版本
funcs_wrong = []
for i in range(3):
    funcs_wrong.append(lambda: i)  # 所有 lambda 引用同一个 i

print("错误版本（全是 2）：", [f() for f in funcs_wrong])  # [2, 2, 2]

# 正确版本 1：用默认参数捕获当前值
funcs_right = []
for i in range(3):
    funcs_right.append(lambda i=i: i)  # 用默认参数 "快照" 当前 i

print("正确版本1（默认参数）：", [f() for f in funcs_right])  # [0, 1, 2]

# 正确版本 2：用闭包包一层（≈ JS 的 IIFE）
funcs_right2 = []
for i in range(3):

    def make_func(val):
        return lambda: val

    funcs_right2.append(make_func(i))

print("正确版本2（闭包包裹）：", [f() for f in funcs_right2])  # [0, 1, 2]


print("\n[OK] Part 1 闭包 完成")
