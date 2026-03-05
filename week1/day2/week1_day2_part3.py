# ============================================================
# 第 1 周 Day 2 - Part 3：生成器（Generator）
# ============================================================
#
# 前端类比：
# - 生成器 ≈ JS 的 function*  / yield
# - Python 的生成器和 JS 几乎一样，语法稍有不同
# - 【AI 场景关键】：ChatGPT 的流式输出（打字机效果）底层就是生成器
#
# 核心概念：惰性求值（Lazy Evaluation）
# - 列表推导式 [x for x in range(1亿)]  → 一次性塞进内存，爆掉
# - 生成器表达式 (x for x in range(1亿)) → 要一个给一个，不爆内存
# ============================================================

import sys
import time


# ============================================================
# 3.1 生成器基础：yield 关键字
# ============================================================

# JS 版本:
# function* count() { yield 1; yield 2; yield 3; }
# const gen = count(); gen.next() → {value: 1, done: false}


# Python 版本:
def count_up_to(n):
    """生成器函数：从 1 数到 n"""
    i = 1
    while i <= n:
        yield i  # 暂停并返回值（≈ JS 的 yield）
        i += 1  # 下次调用时从这里继续


print("--- 3.1 生成器基础 ---")

# 方式 1：用 next() 手动迭代（≈ JS 的 gen.next()）
gen = count_up_to(3)
print(f"next(gen) = {next(gen)}")  # 1
print(f"next(gen) = {next(gen)}")  # 2
print(f"next(gen) = {next(gen)}")  # 3
# next(gen) 再调用就会抛 StopIteration（≈ JS 的 {done: true}）

# 方式 2：用 for 循环自动迭代（最常用）
print("for 循环遍历：", end=" ")
for num in count_up_to(5):
    print(num, end=" ")
print()


# ============================================================
# 3.2 生成器 vs 列表：内存对比
# ============================================================

print("\n--- 3.2 内存对比 ---")

# 列表：一次性全部加载到内存
big_list = [i for i in range(100_000)]
print(f"列表占内存: {sys.getsizeof(big_list):,} bytes")  # ~800KB

# 生成器：几乎不占内存
big_gen = (i for i in range(100_000))
print(f"生成器占内存: {sys.getsizeof(big_gen)} bytes")  # ~200 bytes

# 【面试考点】生成器只能遍历一次！
gen = (x for x in range(5))
first_pass = list(gen)  # [0, 1, 2, 3, 4]
second_pass = list(gen)  # [] ← 空了！已经耗尽
print(f"\n第一次遍历: {first_pass}")
print(f"第二次遍历: {second_pass}  ← 空了！生成器是一次性的")


# ============================================================
# 3.3 yield 的暂停与恢复（理解执行流程）
# ============================================================


def debug_generator():
    """带调试信息的生成器，展示执行流程"""
    print("  [1] 函数开始执行")
    yield "first"
    print("  [2] 第一个 yield 之后恢复")
    yield "second"
    print("  [3] 第二个 yield 之后恢复")
    yield "third"
    print("  [4] 函数结束（会触发 StopIteration）")


print("\n--- 3.3 执行流程追踪 ---")
gen = debug_generator()
print(f"创建生成器（还没执行任何代码）")
print(f"调用 next(): '{next(gen)}'")  # 执行到第一个 yield
print(f"调用 next(): '{next(gen)}'")  # 从第一个 yield 恢复，执行到第二个
print(f"调用 next(): '{next(gen)}'")  # 从第二个 yield 恢复，执行到第三个


# ============================================================
# 3.4 yield from —— 委托生成器（Python 特有，JS 用 yield*）
# ============================================================


def gen_abc():
    yield "A"
    yield "B"
    yield "C"


def gen_123():
    yield 1
    yield 2
    yield 3


# 不用 yield from（麻烦）
def combined_ugly():
    for item in gen_abc():
        yield item
    for item in gen_123():
        yield item


# 用 yield from（优雅）—— ≈ JS 的 yield*
def combined_nice():
    yield from gen_abc()  # 委托给另一个生成器
    yield from gen_123()
    yield from range(10, 13)  # 任何可迭代对象都行


print("\n--- 3.4 yield from ---")
print("yield from 合并:", list(combined_nice()))


# ============================================================
# 3.5 生成器的 send() 方法 —— 双向通信
# ============================================================

# JS: gen.next(value) 可以向生成器发送值
# Python: gen.send(value) 一样


def accumulator():
    """累加器：外部可以 send 值进来"""
    total = 0
    while True:
        value = yield total  # yield 返回当前 total，同时接收外部 send 的值
        if value is None:
            break
        total += value


print("\n--- 3.5 send() 双向通信 ---")
acc = accumulator()
next(acc)  # 启动生成器（第一次必须用 next 或 send(None)）
print(f"send(10): {acc.send(10)}")  # total = 10
print(f"send(20): {acc.send(20)}")  # total = 30
print(f"send(5):  {acc.send(5)}")  # total = 35


# ============================================================
# 3.6 【核心应用】模拟 LLM 流式输出（AI 开发必备技能）
# ============================================================


def stream_llm_response(text, delay=0.02):
    """
    模拟大模型流式输出 —— ChatGPT 打字机效果的核心原理

    真实场景：
    - OpenAI API 设置 stream=True 后，返回的就是一个生成器
    - 每次 yield 一个 token（几个字符）
    - 前端通过 SSE（Server-Sent Events）接收并实时渲染

    你的前端优势：你知道前端怎么消费 SSE，
    现在你学会了后端怎么用生成器产出 SSE
    """
    words = text.split()
    for i, word in enumerate(words):
        time.sleep(delay)  # 模拟模型推理延迟
        # 真实场景中这里 yield 的是 SSE 格式的数据
        yield word + (" " if i < len(words) - 1 else "")


print("\n--- 3.6 模拟 LLM 流式输出 ---")
print("AI: ", end="", flush=True)
for token in stream_llm_response(
    "AGI is the future of artificial intelligence and it will change everything."
):
    print(token, end="", flush=True)
print()  # 换行


# 更接近真实的 FastAPI 流式响应写法
def fake_openai_stream(prompt):
    """模拟 OpenAI 流式 API 的响应格式"""
    response_text = f"The answer to '{prompt}' is: AI will transform the world."
    for char in response_text:
        yield {"choices": [{"delta": {"content": char}, "finish_reason": None}]}
    # 最后发送结束信号
    yield {"choices": [{"delta": {}, "finish_reason": "stop"}]}


print("\n模拟 OpenAI 流式响应：")
full_response = ""
for chunk in fake_openai_stream("What is AGI?"):
    content = chunk["choices"][0]["delta"].get("content", "")
    full_response += content

print(f"  完整响应: {full_response}")


# ============================================================
# 3.7 生成器实战：处理大文件（AI 数据处理场景）
# ============================================================


def read_large_file_lines(filepath, chunk_size=1024):
    """
    逐行读取大文件 —— 处理训练数据时必备

    场景：微调模型时需要处理几个 GB 的 JSONL 文件
    如果一次性 readlines()，内存直接爆
    用生成器逐行处理，内存始终稳定
    """
    # 这里用模拟数据代替文件读取
    fake_lines = [
        '{"instruction": "What is AI?", "output": "AI is..."}',
        '{"instruction": "Explain ML", "output": "ML is..."}',
        '{"instruction": "What is NLP?", "output": "NLP is..."}',
    ]
    for line in fake_lines:
        yield line.strip()


def process_training_data(filepath):
    """处理训练数据：过滤 + 转换（用生成器管道串联）"""
    # 生成器管道：读取 → 解析 → 过滤 → 转换
    # 每一步都是惰性的，不会一次性加载全部数据
    import json

    lines = read_large_file_lines(filepath)  # 第 1 层：读取
    records = (json.loads(line) for line in lines)  # 第 2 层：解析
    valid = (r for r in records if len(r["output"]) > 5)  # 第 3 层：过滤
    formatted = (  # 第 4 层：转换
        f"Q: {r['instruction']}\nA: {r['output']}" for r in valid
    )
    return formatted


print("\n--- 3.7 生成器管道处理数据 ---")
for item in process_training_data("fake_path.jsonl"):
    print(f"  {item}")


print("\n[OK] Part 3 生成器 完成")
