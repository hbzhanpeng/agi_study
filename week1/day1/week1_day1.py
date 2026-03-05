# ============================================================
# 第 1 周 Day 1：Python 基础语法与数据结构
# 运行方式：python week1_day1.py
# ============================================================


# ============================================================
# 第一部分：变量与类型 —— 对标 JS 的 let/const/var
# ============================================================

# Python 没有 let/const/var，直接赋值
name = "前端转 AGI"  # str  (≈ JS string)
age = 25  # int  (≈ JS number，但 Python 区分 int 和 float)
salary = 35000.50  # float
is_learning = True  # bool (注意大写 True/False，不是 true/false)
nothing = None  # NoneType (≈ JS null，Python 没有 undefined)

# 【面试考点】Python 是强类型 + 动态类型
# 强类型：不会自动转换，"1" + 1 会报错（JS 会得到 "11"）
# 动态类型：变量不需要声明类型，运行时确定
try:
    result = "1" + 1  # TypeError! Python 不会隐式转换
except TypeError as e:
    print(f"强类型演示：'1' + 1 报错 → {e}")

# 正确做法：显式转换
result = int("1") + 1  # 2
print(f"显式转换：int('1') + 1 = {result}")


# 类型标注（≈ TypeScript，但不强制）
def greet(name: str, times: int = 1) -> str:
    """类型标注不影响运行，但 IDE 会帮你检查"""
    return f"Hello {name}! " * times


print(greet("AGI", 3))

print("\n" + "=" * 60)
print("第二部分：List（列表）—— 对标 JS Array")
print("=" * 60)

# ============================================================
# 第二部分：List —— 对标 JS Array
# ============================================================

# 创建
# JS:  const arr = [1, 2, 3]
# Py:  直接写
nums = [1, 2, 3, 4, 5]
mixed = [1, "hello", True, [1, 2]]  # 和 JS 一样可以混合类型

# ---- 增删改查 ----
# JS: arr.push(6)       →  Py: arr.append(6)
# JS: arr.unshift(0)    →  Py: arr.insert(0, 0)
# JS: arr.pop()         →  Py: arr.pop()
# JS: arr.splice(1,1)   →  Py: del arr[1] 或 arr.pop(1)
# JS: arr.includes(3)   →  Py: 3 in arr
# JS: arr.indexOf(3)    →  Py: arr.index(3)
# JS: arr.length        →  Py: len(arr)

fruits = ["apple", "banana", "cherry"]
fruits.append("date")  # 末尾添加
fruits.insert(0, "avocado")  # 指定位置插入
removed = fruits.pop()  # 弹出末尾，返回被弹出的元素
print(f"水果列表：{fruits}")
print(f"被移除的：{removed}")
print(f"cherry 在不在：{'cherry' in fruits}")
print(f"列表长度：{len(fruits)}")

# ---- 【重点】切片（Slicing）—— JS 没有这么强大的东西 ----
# 语法：list[start:stop:step]  (start 包含，stop 不包含)
nums = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

print(f"\n--- 切片演示 ---")
print(f"原始列表：{nums}")
print(f"nums[2:5]   = {nums[2:5]}")  # [2, 3, 4]  取索引 2 到 4
print(f"nums[:3]    = {nums[:3]}")  # [0, 1, 2]  从头取 3 个
print(f"nums[-3:]   = {nums[-3:]}")  # [7, 8, 9]  取最后 3 个
print(f"nums[::2]   = {nums[::2]}")  # [0, 2, 4, 6, 8]  每隔一个取一个
print(f"nums[::-1]  = {nums[::-1]}")  # [9, 8, ..., 0]  反转！

# 【面试考点】切片返回的是新列表（浅拷贝）
a = [1, 2, 3]
b = a[:]  # 浅拷贝，等价于 a.copy()
b.append(4)
print(f"\n切片是浅拷贝：a={a}, b={b}")  # a 不受影响

# ---- 排序 ----
# JS: arr.sort((a,b) => a-b)
# Py: arr.sort() 或 sorted(arr)
numbers = [3, 1, 4, 1, 5, 9, 2, 6]
print(f"\n原始：{numbers}")
print(f"sorted()（不改原列表）：{sorted(numbers)}")
numbers.sort()  # 原地排序
print(f".sort()（改了原列表）：{numbers}")

# 自定义排序（≈ JS 的 sort 回调）
words = ["banana", "apple", "cherry", "date"]
words.sort(key=len)  # 按长度排序
print(f"按长度排序：{words}")

# 按对象属性排序（超级常用）
students = [
    {"name": "Alice", "score": 85},
    {"name": "Bob", "score": 92},
    {"name": "Charlie", "score": 78},
]
students.sort(key=lambda s: s["score"], reverse=True)
print(f"按分数降序：{[s['name'] for s in students]}")


print("\n" + "=" * 60)
print("第三部分：Dict（字典）—— 对标 JS Object / Map")
print("=" * 60)

# ============================================================
# 第三部分：Dict —— 对标 JS Object / Map
# ============================================================

# 创建
# JS: const obj = { name: "Tom", age: 25 }
# Py: dict 的 key 必须是不可变类型（str, int, tuple），不能是 list
person = {"name": "Tom", "age": 25, "skills": ["Python", "React"]}

# ---- 增删改查 ----
# JS: obj.name 或 obj["name"]  →  Py: 只能 dict["key"]（不能 dict.key）
# JS: obj.email = "x@y.com"   →  Py: dict["email"] = "x@y.com"
# JS: delete obj.email         →  Py: del dict["email"]
# JS: "name" in obj            →  Py: "name" in dict

print(f"取值：{person['name']}")
person["email"] = "tom@agi.com"  # 新增
person["age"] = 26  # 修改
print(f"修改后：{person}")

# 【重点】安全取值（避免 KeyError）
# JS: obj.phone ?? "N/A"
# Py: dict.get("phone", "N/A")
phone = person.get("phone", "N/A")
print(f"安全取值：{phone}")

# ---- 遍历 ----
print(f"\n--- 遍历演示 ---")

# 遍历 key
for key in person:
    print(f"  key: {key}")

# 遍历 key-value（最常用）
# ≈ JS: Object.entries(obj).forEach(([k,v]) => ...)
for key, value in person.items():
    print(f"  {key}: {value}")

# ---- 合并 ----
# JS: { ...obj1, ...obj2 }
# Py 3.9+: dict1 | dict2
defaults = {"theme": "dark", "lang": "en"}
user_prefs = {"lang": "zh", "font_size": 14}
merged = defaults | user_prefs  # 后者覆盖前者
print(f"\n合并字典：{merged}")

# 【面试考点】dict 的底层是哈希表
# - 查找 O(1)，和 JS Object 一样
# - Python 3.7+ dict 保持插入顺序（面试常问）
# - key 必须是可哈希的（不可变类型）


print("\n" + "=" * 60)
print("第四部分：Set（集合）—— 和 JS Set 几乎一样")
print("=" * 60)

# ============================================================
# 第四部分：Set —— 和 JS Set 几乎一样
# ============================================================

# 创建
# JS: new Set([1,2,3])
# Py: {1, 2, 3} 或 set([1, 2, 3])
a = {1, 2, 3, 4, 5}
b = {4, 5, 6, 7, 8}

# ---- 集合运算（JS Set 没有这些，Python 的优势！）----
print(f"并集 a | b = {a | b}")  # {1,2,3,4,5,6,7,8}
print(f"交集 a & b = {a & b}")  # {4, 5}
print(f"差集 a - b = {a - b}")  # {1, 2, 3}
print(f"对称差 a ^ b = {a ^ b}")  # {1, 2, 3, 6, 7, 8}

# 【实用场景】去重
nums_with_dups = [1, 2, 2, 3, 3, 3, 4]
unique = list(set(nums_with_dups))
print(f"\n去重：{unique}")

# 【面试考点】frozenset —— 不可变集合，可以当 dict 的 key
fs = frozenset([1, 2, 3])
print(f"frozenset: {fs}")


print("\n" + "=" * 60)
print("第五部分：Tuple（元组）—— JS 没有直接对标")
print("=" * 60)

# ============================================================
# 第五部分：Tuple —— 不可变的 list
# ============================================================

# 创建
# 可以理解为 Object.freeze([1, 2, 3])，但更轻量
point = (10, 20)
rgb = (255, 128, 0)

# 取值和 list 一样，但不能修改
print(f"point[0] = {point[0]}")
try:
    point[0] = 99  # TypeError!
except TypeError as e:
    print(f"tuple 不可变：{e}")

# 【重点】解构赋值（≈ JS 的解构）
# JS: const [x, y] = point
# Py: x, y = point
x, y = point
print(f"解构：x={x}, y={y}")

# 交换变量（Python 独有的优雅写法）
a, b = 1, 2
a, b = b, a  # 一行交换！JS 需要 [a,b] = [b,a]
print(f"交换后：a={a}, b={b}")


# 函数返回多个值（实际上返回的是 tuple）
def get_user():
    return "Tom", 25, "tom@agi.com"


name, age, email = get_user()
print(f"多返回值：{name}, {age}, {email}")

# 【面试考点】tuple 可以作为 dict 的 key，list 不行
location_scores = {
    (0, 0): "origin",
    (1, 1): "diagonal",
}
print(f"\ntuple 做 key：{location_scores[(0, 0)]}")


print("\n" + "=" * 60)
print("第六部分：推导式 —— 对标 JS 的 map/filter 链式调用")
print("=" * 60)

# ============================================================
# 第六部分：推导式（Comprehension）—— Python 最优雅的特性
# ============================================================

# ---- 列表推导式（最常用）----

# JS: [1,2,3,4,5].map(x => x * x)
# Py: [x * x for x in range(1, 6)]
squares = [x * x for x in range(1, 6)]
print(f"平方：{squares}")  # [1, 4, 9, 16, 25]

# JS: [1,2,3,4,5].filter(x => x % 2 === 0)
# Py: [x for x in range(1, 6) if x % 2 == 0]
evens = [x for x in range(1, 6) if x % 2 == 0]
print(f"偶数：{evens}")  # [2, 4]

# JS: [1,2,3,4,5].filter(x => x % 2 === 0).map(x => x * x)
# Py: 一行搞定 filter + map
even_squares = [x * x for x in range(1, 6) if x % 2 == 0]
print(f"偶数的平方：{even_squares}")  # [4, 16]

# 嵌套推导式（≈ JS 的 flatMap）
# JS: [[1,2],[3,4]].flatMap(arr => arr)
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [num for row in matrix for num in row]
print(f"展平矩阵：{flat}")

# ---- 字典推导式 ----
# JS: Object.fromEntries(arr.map(x => [x, x*x]))
square_dict = {x: x * x for x in range(1, 6)}
print(f"\n字典推导：{square_dict}")

# 实用：反转字典的 key-value
original = {"a": 1, "b": 2, "c": 3}
reversed_dict = {v: k for k, v in original.items()}
print(f"反转字典：{reversed_dict}")

# ---- 集合推导式 ----
unique_lengths = {len(word) for word in ["hello", "world", "hi", "hey"]}
print(f"\n集合推导（去重长度）：{unique_lengths}")

# ---- 生成器表达式（省内存版推导式）----
# 用 () 代替 []，不会一次性生成所有元素
# ≈ JS 的 generator function
total = sum(x * x for x in range(1_000_000))  # 不会占用大量内存
print(f"\n生成器求和（100万个数的平方和）：{total}")


print("\n" + "=" * 60)
print("第七部分：常用内置函数速查")
print("=" * 60)

# ============================================================
# 第七部分：常用内置函数
# ============================================================

nums = [3, 1, 4, 1, 5, 9, 2, 6]

# enumerate —— 带索引遍历（≈ JS forEach 的 index 参数）
# JS: arr.forEach((item, index) => ...)
# Py: for i, item in enumerate(arr):
print("enumerate 演示：")
for i, num in enumerate(nums):
    if i < 3:  # 只打印前 3 个
        print(f"  索引 {i}: 值 {num}")

# zip —— 并行遍历多个列表（JS 没有直接对应）
names = ["Alice", "Bob", "Charlie"]
scores = [85, 92, 78]
for name, score in zip(names, scores):
    print(f"  {name}: {score}分")

# map / filter（函数式，但 Python 更推荐用推导式）
doubled = list(map(lambda x: x * 2, nums))
print(f"\nmap 加倍：{doubled}")

big = list(filter(lambda x: x > 4, nums))
print(f"filter 大于4：{big}")

# any / all（≈ JS 的 some / every）
has_big = any(x > 8 for x in nums)  # ≈ nums.some(x => x > 8)
all_positive = all(x > 0 for x in nums)  # ≈ nums.every(x => x > 0)
print(f"\nany > 8: {has_big}")
print(f"all > 0: {all_positive}")


print("\n" + "=" * 60)
print("第八部分：字符串（对标 JS 模板字符串）")
print("=" * 60)

# ============================================================
# 第八部分：字符串操作
# ============================================================

# f-string（≈ JS 的模板字符串 `${}`）
name = "AGI"
version = 4.0
print(f"Hello {name} v{version}!")  # ≈ `Hello ${name} v${version}!`

# 常用方法（和 JS 的 String 方法几乎对应）
text = "  Hello, AGI World!  "
print(f"strip()  = '{text.strip()}'")  # ≈ trim()
print(f"split()  = {text.strip().split(' ')}")  # ≈ split(' ')
print(f"replace  = {text.replace('AGI', 'AI')}")
print(f"upper    = {text.upper()}")
print(f"startswith = {text.strip().startswith('Hello')}")

# 多行字符串（≈ JS 的反引号 `` ）
prompt = """你是一个 AI 助手。
请回答以下问题：
什么是 AGI？"""
print(f"\n多行字符串：\n{prompt}")

# 字符串格式化对比
# JS:  `${name} is ${age} years old`
# Py:  f"{name} is {age} years old"        ← 推荐
# Py:  "{} is {} years old".format(name, age)
# Py:  "%s is %d years old" % (name, age)  ← 老式

print("\n" + "=" * 60)
print("[OK] Day 1 代码全部运行完毕！")
print("=" * 60)
