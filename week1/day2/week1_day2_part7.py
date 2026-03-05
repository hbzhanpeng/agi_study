# ============================================================
# 第 1 周 Day 2 - Part 7：LeetCode 算法实战
# ============================================================
#
# 原则：用今天学的 闭包/装饰器/生成器 + Day1 的数据结构 解题
# 每道题标注：难度、面试频率、考察知识点
# ============================================================

import time
from functools import wraps


# ---- 通用工具：计时 + 测试装饰器（复用今天学的装饰器）----


def test_case(func):
    """自动化测试装饰器：运行测试用例并校验结果"""

    @wraps(func)
    def wrapper():
        print(f"\n{'=' * 60}")
        print(f"题目: {func.__name__}")
        if func.__doc__:
            print(f"说明: {func.__doc__.strip()}")
        print(f"{'=' * 60}")
        func()
        print(f"[PASS] {func.__name__} 全部通过")

    return wrapper


def assert_equal(actual, expected, label=""):
    """断言工具"""
    if actual == expected:
        print(f"  [OK] {label}: {actual}")
    else:
        print(f"  [FAIL] {label}: 期望 {expected}，实际 {actual}")
        raise AssertionError(f"{label} failed")


class AssertionError(Exception):
    pass


# ============================================================
# 题目 1：LeetCode 20. 有效的括号（Easy）
# ============================================================
# 面试频率：★★★★★（几乎必考）
# 考察：栈（用 list 模拟）、dict 映射
# 和 AI 的关联：解析 JSON/XML 格式的模型输出时需要括号匹配


@test_case
def valid_parentheses():
    """LeetCode 20: 判断括号字符串是否有效"""

    def is_valid(s: str) -> bool:
        # 用 dict 存储括号映射（Day1 知识）
        mapping = {")": "(", "]": "[", "}": "{"}
        # 用 list 当栈（Day1 知识）
        stack = []

        for char in s:
            if char in mapping:
                # 遇到右括号：弹出栈顶，检查是否匹配
                top = stack.pop() if stack else "#"
                if top != mapping[char]:
                    return False
            else:
                # 遇到左括号：压栈
                stack.append(char)

        # 栈为空说明全部匹配
        return len(stack) == 0

    # 测试用例
    assert_equal(is_valid("()"), True, "基础")
    assert_equal(is_valid("()[]{}"), True, "多种括号")
    assert_equal(is_valid("(]"), False, "不匹配")
    assert_equal(is_valid("([)]"), False, "交叉")
    assert_equal(is_valid("{[]}"), True, "嵌套")
    assert_equal(is_valid(""), True, "空字符串")
    assert_equal(is_valid("(("), False, "未闭合")


valid_parentheses()


# ============================================================
# 题目 2：LeetCode 1. 两数之和（Easy）
# ============================================================
# 面试频率：★★★★★（经典中的经典）
# 考察：dict 哈希查找 O(1)、一次遍历思路
# 和 AI 的关联：向量检索中的"找到最匹配的"思想类似


@test_case
def two_sum():
    """LeetCode 1: 找到数组中两个数之和等于 target 的下标"""

    def two_sum_solution(nums: list, target: int) -> list:
        # 哈希表法：边遍历边查找
        # key: 数值，value: 下标
        seen = {}  # dict 查找 O(1)（Day1 知识）

        for i, num in enumerate(nums):  # enumerate（Day1 知识）
            complement = target - num
            if complement in seen:  # dict 的 in 操作 O(1)
                return [seen[complement], i]
            seen[num] = i

        return []

    assert_equal(two_sum_solution([2, 7, 11, 15], 9), [0, 1], "基础")
    assert_equal(two_sum_solution([3, 2, 4], 6), [1, 2], "非首位")
    assert_equal(two_sum_solution([3, 3], 6), [0, 1], "重复元素")


two_sum()


# ============================================================
# 题目 3：LeetCode 49. 字母异位词分组（Medium）
# ============================================================
# 面试频率：★★★★（中等偏高）
# 考察：dict + tuple 做 key + 排序（Day1 + Day2 知识综合）
# 和 AI 的关联：文本聚类、相似文档分组的简化版


@test_case
def group_anagrams():
    """LeetCode 49: 将字母异位词分组"""

    def group_anagrams_solution(strs: list) -> list:
        # 思路：排序后的字符串作为 key，原始字符串作为 value
        # tuple 可以做 dict 的 key，list 不行（Day1 知识）
        groups = {}  # key: tuple(sorted(word)), value: [words...]

        for word in strs:
            # sorted() 返回 list，转 tuple 才能做 dict 的 key
            key = tuple(sorted(word))
            if key not in groups:
                groups[key] = []
            groups[key].append(word)

        return list(groups.values())

    result = group_anagrams_solution(["eat", "tea", "tan", "ate", "nat", "bat"])
    # 排序后比较（因为组内顺序和组间顺序可能不同）
    result_sorted = sorted([sorted(group) for group in result])
    expected_sorted = sorted(
        [sorted(g) for g in [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]]
    )
    assert_equal(result_sorted, expected_sorted, "基础")

    result2 = group_anagrams_solution([""])
    assert_equal(result2, [[""]], "空字符串")


group_anagrams()


# ============================================================
# 题目 4：LeetCode 341. 扁平化嵌套列表迭代器（Medium）
# ============================================================
# 面试频率：★★★★（考生成器 + 递归）
# 考察：生成器 yield from（今天 Part 3 核心知识）
# 和 AI 的关联：处理嵌套 JSON 结构（模型输出经常是嵌套的）


@test_case
def flatten_nested_list():
    """LeetCode 341 简化版: 用生成器拍平嵌套列表"""

    def flatten(nested):
        """递归生成器 —— yield from 的经典应用"""
        for item in nested:
            if isinstance(item, list):
                yield from flatten(item)  # 递归委托（Day2 Part 3 知识）
            else:
                yield item

    # 测试
    assert_equal(
        list(flatten([1, [2, [3, 4], 5], [6, 7]])), [1, 2, 3, 4, 5, 6, 7], "基础嵌套"
    )
    assert_equal(list(flatten([1, [2], [[3]], [[[4]]]])), [1, 2, 3, 4], "深层嵌套")
    assert_equal(list(flatten([])), [], "空列表")
    assert_equal(list(flatten([1, 2, 3])), [1, 2, 3], "无嵌套")


flatten_nested_list()


# ============================================================
# 题目 5：LeetCode 146. LRU 缓存（Medium）★★★★★
# ============================================================
# 面试频率：★★★★★（大厂必考）
# 考察：dict + 双向链表（或 OrderedDict）、闭包/类设计
# 和 AI 的关联：LLM 推理缓存（KV Cache）、语义缓存 的简化版
#
# 这道题直接关联 AI 面试高频问题：
# "什么是 KV Cache？" → 本质就是一个 LRU 缓存

from collections import OrderedDict


@test_case
def lru_cache_impl():
    """LeetCode 146: 实现 LRU（最近最少使用）缓存"""

    class LRUCache:
        """
        LRU 缓存实现

        思路：用 OrderedDict（有序字典）
        - get: 访问后移到末尾（最近使用）
        - put: 插入末尾，超过容量时删除头部（最久未使用）

        面试时先说 OrderedDict 方案，再说可以用 dict + 双向链表手写
        """

        def __init__(self, capacity: int):
            self.capacity = capacity
            self.cache = OrderedDict()

        def get(self, key: int) -> int:
            if key not in self.cache:
                return -1
            # 移到末尾（标记为最近使用）
            self.cache.move_to_end(key)
            return self.cache[key]

        def put(self, key: int, value: int) -> None:
            if key in self.cache:
                # 已存在：更新值 + 移到末尾
                self.cache.move_to_end(key)
            self.cache[key] = value

            if len(self.cache) > self.capacity:
                # 超过容量：删除头部（最久未使用）
                # last=False 表示删除头部
                self.cache.popitem(last=False)

    # 测试（LeetCode 官方用例）
    cache = LRUCache(2)
    cache.put(1, 1)  # 缓存: {1=1}
    cache.put(2, 2)  # 缓存: {1=1, 2=2}
    assert_equal(cache.get(1), 1, "get(1)")  # 返回 1，缓存: {2=2, 1=1}
    cache.put(3, 3)  # 淘汰 key=2，缓存: {1=1, 3=3}
    assert_equal(cache.get(2), -1, "get(2)")  # 返回 -1（已被淘汰）
    cache.put(4, 4)  # 淘汰 key=1，缓存: {3=3, 4=4}
    assert_equal(cache.get(1), -1, "get(1) again")  # 返回 -1（已被淘汰）
    assert_equal(cache.get(3), 3, "get(3)")  # 返回 3
    assert_equal(cache.get(4), 4, "get(4)")  # 返回 4


lru_cache_impl()


# ============================================================
# 题目 6：用装饰器 + 闭包解题 —— 斐波那契 + 记忆化
# ============================================================
# 面试频率：★★★★（考装饰器实际应用）
# 考察：装饰器、闭包缓存、递归优化
# 和 AI 的关联：动态规划思想 → 模型推理中的缓存复用


@test_case
def fibonacci_with_memo():
    """用自己写的 @memoize 装饰器优化斐波那契"""

    # 手写 memoize（不用 functools.lru_cache）
    def memoize(func):
        cache = {}  # 闭包变量

        @wraps(func)
        def wrapper(*args):
            if args not in cache:
                cache[args] = func(*args)
            return cache[args]

        wrapper.cache = cache  # 暴露缓存供调试
        return wrapper

    @memoize
    def fib(n):
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)

    # 没有 memoize：fib(40) 要算几十秒
    # 有 memoize：瞬间完成
    start = time.perf_counter()

    assert_equal(fib(0), 0, "fib(0)")
    assert_equal(fib(1), 1, "fib(1)")
    assert_equal(fib(10), 55, "fib(10)")
    assert_equal(fib(30), 832040, "fib(30)")
    assert_equal(fib(50), 12586269025, "fib(50)")

    elapsed = time.perf_counter() - start
    print(f"  fib(50) 耗时: {elapsed:.4f}s（有缓存，瞬间完成）")
    print(f"  缓存大小: {len(fib.cache)} 个条目")


fibonacci_with_memo()


# ============================================================
# 题目 7：用生成器解题 —— 无限序列 + itertools
# ============================================================
# 面试频率：★★★（考生成器的实际运用能力）
# 考察：生成器、itertools、惰性求值

from itertools import islice, takewhile, count


@test_case
def generator_algorithms():
    """生成器在算法中的应用"""

    # 7.1 素数生成器（埃拉托斯特尼筛法的生成器版本）
    def primes():
        """无限素数生成器"""
        yield 2
        candidate = 3
        found_primes = [2]
        while True:
            # 检查 candidate 是否能被已知素数整除
            is_prime = all(
                candidate % p != 0 for p in found_primes if p * p <= candidate
            )
            if is_prime:
                found_primes.append(candidate)
                yield candidate
            candidate += 2  # 跳过偶数

    # 取前 10 个素数（用 islice 切片生成器）
    first_10_primes = list(islice(primes(), 10))
    assert_equal(first_10_primes, [2, 3, 5, 7, 11, 13, 17, 19, 23, 29], "前10个素数")

    # 7.2 滑动窗口生成器（面试常考 + AI 中文本分块会用）
    def sliding_window(iterable, size):
        """
        滑动窗口生成器

        AI 场景：文本按固定窗口大小分块（Chunking）
        比如把一篇文章按 512 token 的窗口切分
        """
        from collections import deque

        window = deque(maxlen=size)

        for item in iterable:
            window.append(item)
            if len(window) == size:
                yield tuple(window)

    windows = list(sliding_window([1, 2, 3, 4, 5, 6], 3))
    assert_equal(windows, [(1, 2, 3), (2, 3, 4), (3, 4, 5), (4, 5, 6)], "滑动窗口")

    # 文本分块示例
    text = "我 是 一 个 AI 助 手 很 高 兴 认 识 你"
    chars = text.split()
    chunks = [" ".join(w) for w in sliding_window(chars, 4)]
    print(f"  文本分块: {chunks}")

    # 7.3 用生成器实现 zip 的增强版（longest）
    def zip_longest_gen(*iterables, fillvalue=None):
        """自己实现 itertools.zip_longest"""
        iterators = [iter(it) for it in iterables]
        while True:
            values = []
            all_done = True
            for it in iterators:
                try:
                    values.append(next(it))
                    all_done = False
                except StopIteration:
                    values.append(fillvalue)
            if all_done:
                return
            yield tuple(values)

    result = list(zip_longest_gen([1, 2, 3], ["a", "b"], fillvalue="-"))
    assert_equal(result, [(1, "a"), (2, "b"), (3, "-")], "zip_longest")


generator_algorithms()


print(f"\n{'=' * 60}")
print(f"[OK] Day 2 全部 7 个 Part 完成！")
print(f"{'=' * 60}")
