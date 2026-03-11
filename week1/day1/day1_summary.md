# 第 1 周 Day 1 学习总结：Python 基础语法与数据结构

> **核心目标：跨越语法门槛，掌握 Python 四大核心数据结构，能用 Python 思考逻辑。**

---

## 1. 为什么要学 Python 基础？

```
前端工程师转 AGI 开发，Python 是第一道门槛：
- 所有 AI 框架（LangChain/HuggingFace/PyTorch）都是 Python
- 数据处理、模型调用、API 开发全靠 Python
- 不懂 Python 语法，看不懂任何 AI 代码

好消息：有 JS 基础，Python 上手只需 1 天
```

---

## 2. 语法对比：JS → Python

| JS 写法 | Python 写法 | 说明 |
|---------|------------|------|
| `let name = "AGI"` | `name = "AGI"` | 无需声明关键字 |
| `console.log(x)` | `print(x)` | 打印输出 |
| `true / false / null` | `True / False / None` | 首字母大写！ |
| `{}` 和 `;` 划分代码块 | **缩进**（4个空格）划分 | Python 靠缩进，不靠括号 |
| `// 注释` | `# 注释` | 单行注释 |
| `/* 多行 */` | `""" 多行 """` | 多行注释/文档字符串 |

**最容易踩的坑**：
```python
# ❌ 缩进错误，Python 直接报错
if True:
print("hello")  # IndentationError!

# ✅ 正确
if True:
    print("hello")
```

---

## 3. 四大核心数据结构

### 3.1 List（列表）— 对应 JS Array

```python
nums = [1, 2, 3, 4, 5]

# 增删
nums.append(6)       # 末尾添加
nums.pop()           # 删除末尾
nums.insert(0, 0)    # 指定位置插入

# 切片（Python 独有杀器）
nums[1:3]    # [2, 3]  从索引1到3（不含3）
nums[:3]     # [1, 2, 3]  前3个
nums[-1]     # 5  最后一个
nums[::-1]   # [5,4,3,2,1]  反转
```

**面试考点**：切片不会修改原列表，返回新列表。

### 3.2 Dict（字典）— 对应 JS Object/Map

```python
user = {"name": "张三", "age": 25}

# 读取
user["name"]              # "张三"（不存在会报 KeyError）
user.get("email", "无")   # 安全读取，不存在返回默认值

# 遍历
for key, value in user.items():
    print(f"{key}: {value}")

# 常用方法
user.keys()    # dict_keys(['name', 'age'])
user.values()  # dict_values(['张三', 25])
```

**面试考点**：`user["key"]` vs `user.get("key")` 的区别——前者不存在抛异常，后者返回 None。

### 3.3 Set（集合）— 对应 JS Set

```python
tags = {"python", "ai", "python"}  # 自动去重
print(tags)  # {'python', 'ai'}

# 集合运算（AI 数据处理常用）
a = {1, 2, 3}
b = {2, 3, 4}
a & b   # {2, 3}  交集
a | b   # {1, 2, 3, 4}  并集
a - b   # {1}  差集
```

**面试考点**：快速去重 `list(set(my_list))`，但会丢失顺序。

### 3.4 Tuple（元组）— JS 没有对应

```python
point = (10, 20)   # 不可变，创建后不能修改
x, y = point       # 解包（非常常用）

# 为什么需要 Tuple？
# 1. 作为字典的 key（List 不能当 key）
location_map = {(39.9, 116.4): "北京"}

# 2. 函数返回多个值
def get_user():
    return "张三", 25  # 实际上返回的是 Tuple

name, age = get_user()  # 解包接收
```

**面试考点**：Tuple 不可变，可以作为字典的 key；List 可变，不能作为 key。

---

## 4. 推导式（Comprehensions）— Python 独有杀器

**前端类比**：把 `filter()` + `map()` 合二为一，语法更简洁。

```python
nums = [1, 2, 3, 4, 5, 6]

# JS 写法
# nums.filter(n => n % 2 === 0).map(n => n * n)

# Python 推导式：[生成值 for 变量 in 集合 if 条件]
squared_evens = [n * n for n in nums if n % 2 == 0]
# [4, 16, 36]

# 字典推导式（AI 处理数据超常用）
word_lengths = {word: len(word) for word in ["hello", "world", "ai"]}
# {'hello': 5, 'world': 5, 'ai': 2}

# 集合推导式
unique_lengths = {len(word) for word in ["hello", "world", "ai"]}
# {2, 5}
```

**为什么重要**：写 AI 数据处理脚本时，推导式能把 5 行代码压缩成 1 行，是 Pythonic 写法的标志。

---

## 5. 面试考点汇总

### 问法 1："Python 的 List 和 Tuple 有什么区别？"

**标准答案**：
> "List 是可变的，创建后可以增删改；Tuple 是不可变的，创建后不能修改。因为不可变，Tuple 可以作为字典的 key，List 不行。Tuple 通常用于表示固定的数据（如坐标、函数返回多个值），List 用于需要动态修改的数据。"

### 问法 2："如何快速去除列表中的重复元素？"

**标准答案**：
> "`list(set(my_list))`，利用 Set 的唯一性去重。但注意会丢失原来的顺序。如果需要保持顺序，用 `list(dict.fromkeys(my_list))`。"

### 问法 3："Python 的切片是什么？"

**标准答案**：
> "切片是 Python 访问序列子集的语法，格式是 `[start:stop:step]`。不会修改原序列，返回新对象。常用技巧：`[::-1]` 反转，`[:n]` 取前 n 个，`[-n:]` 取后 n 个。"

**加分项**：
- 能说出切片的时间复杂度是 O(k)，k 是切片长度
- 能说出 `dict.get()` 比 `dict[]` 更安全的原因

---

## 6. 真实踩坑经历

**坑 1：可变默认参数**
```python
# ❌ 危险！默认参数只初始化一次，多次调用会共享同一个 list
def add_item(item, items=[]):
    items.append(item)
    return items

add_item(1)  # [1]
add_item(2)  # [1, 2]  ← 不是 [2]！

# ✅ 正确写法
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

**坑 2：字典遍历时修改**
```python
# ❌ 遍历时删除会报 RuntimeError
for key in user:
    if key == "password":
        del user[key]

# ✅ 先复制 keys
for key in list(user.keys()):
    if key == "password":
        del user[key]
```

**坑 3：浅拷贝陷阱**
```python
a = [1, [2, 3]]
b = a.copy()    # 浅拷贝
b[1].append(4)
print(a)  # [1, [2, 3, 4]]  ← a 也被修改了！

# ✅ 深拷贝
import copy
b = copy.deepcopy(a)
```

---

## 7. 知识点关联图

```
Week1 Day1 Python 基础
    ↓ 基础
Day2 函数进阶（装饰器/生成器）
Day3 异步编程（async/await）
    ↓ 应用
Week3 Prompt Engineering（字符串处理）
Week4 RAG（列表/字典处理数据）
Week5 Agent（字典传递工具参数）
```

---

**导师寄语**：
> 第一天的语法只是"磨刀"，但切片和推导式是 Python 区别于前端语言的两大杀器。特别是推导式，写 AI 数据处理脚本时每天都在用。可变默认参数那个坑我当年在生产环境踩过，导致一个 Bug 排查了半天，一定要记住！

**下一步**：Week1 Day2 — 函数进阶（装饰器、生成器、闭包）
