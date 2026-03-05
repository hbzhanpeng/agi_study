# ============================================================
# 第 1 周 Day 3 - Part 2：Threading / Multiprocessing / GIL
# ============================================================
#
# 前端类比：
# | 概念                | JS                      | Python                    |
# |---------------------|-------------------------|---------------------------|
# | 单线程              | 主线程（V8）             | 主线程（CPython + GIL）    |
# | 异步 I/O            | Event Loop + callback   | asyncio                   |
# | 多线程              | Web Workers（有限制）   | threading（有 GIL 限制）   |
# | 多进程              | child_process / cluster | multiprocessing（无 GIL） |
# | 共享内存            | SharedArrayBuffer       | multiprocessing.Value/Array|
#
# 【面试核心问题】Python 的 GIL 是什么？为什么有它？怎么绕过？
# ============================================================

import threading
import multiprocessing
import time
import queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed


# ============================================================
# 2.1 GIL（全局解释器锁）—— 面试 TOP 3 必考题
# ============================================================

print("=" * 60)
print("2.1 GIL 演示：为什么 Python 多线程不能加速 CPU 密集任务")
print("=" * 60)


def cpu_heavy_work(n):
    """CPU 密集型任务：计算大量平方和"""
    total = 0
    for i in range(n):
        total += i * i
    return total


def io_heavy_work(seconds):
    """I/O 密集型任务：模拟网络请求等待"""
    time.sleep(seconds)
    return f"I/O done after {seconds}s"


N = 5_000_000

# ---- CPU 密集型：多线程 vs 单线程 ----
# 单线程
start = time.perf_counter()
cpu_heavy_work(N)
cpu_heavy_work(N)
single_cpu_time = time.perf_counter() - start
print(f"\n[CPU 密集] 单线程: {single_cpu_time:.3f}s")

# 多线程（因为 GIL，不会更快，甚至可能更慢！）
start = time.perf_counter()
t1 = threading.Thread(target=cpu_heavy_work, args=(N,))
t2 = threading.Thread(target=cpu_heavy_work, args=(N,))
t1.start()
t2.start()
t1.join()
t2.join()
multi_thread_cpu_time = time.perf_counter() - start
print(f"[CPU 密集] 多线程: {multi_thread_cpu_time:.3f}s（GIL 限制，没有加速）")

# ---- I/O 密集型：多线程 vs 单线程 ----
# 单线程
start = time.perf_counter()
io_heavy_work(0.2)
io_heavy_work(0.2)
single_io_time = time.perf_counter() - start
print(f"\n[I/O 密集] 单线程: {single_io_time:.3f}s")

# 多线程（GIL 在 I/O 等待时会释放，所以有效！）
start = time.perf_counter()
t1 = threading.Thread(target=io_heavy_work, args=(0.2,))
t2 = threading.Thread(target=io_heavy_work, args=(0.2,))
t1.start()
t2.start()
t1.join()
t2.join()
multi_thread_io_time = time.perf_counter() - start
print(f"[I/O 密集] 多线程: {multi_thread_io_time:.3f}s（GIL 释放，有效加速！）")

print(f"""
【面试答案总结】
GIL（Global Interpreter Lock）= CPython 的全局锁

为什么有 GIL？
  → 保护 CPython 的引用计数内存管理不会被多线程破坏
  → 简化了 C 扩展的开发

GIL 的影响：
  → CPU 密集型：多线程无法加速（同一时刻只有一个线程执行 Python 字节码）
  → I/O 密集型：多线程有效！（I/O 等待时 GIL 会释放）

如何绕过 GIL？
  → 多进程（multiprocessing）：每个进程有独立的 GIL
  → C 扩展（NumPy、Pandas）：在 C 层面释放 GIL
  → asyncio：单线程异步，适合 I/O 密集场景
  → Python 3.13+：实验性的 free-threaded 模式（no-GIL）
""")


# ============================================================
# 2.2 ThreadPoolExecutor —— 生产级线程池（AI 项目标配）
# ============================================================

print("=" * 60)
print("2.2 ThreadPoolExecutor（线程池）")
print("=" * 60)


def fetch_embedding(text: str) -> dict:
    """模拟调用 Embedding API"""
    time.sleep(0.1)  # 模拟网络延迟
    return {"text": text, "embedding": [0.1, 0.2, 0.3]}


texts = [f"document_{i}" for i in range(10)]

# ---- 串行（慢）----
start = time.perf_counter()
serial_results = [fetch_embedding(t) for t in texts]
serial_time = time.perf_counter() - start
print(f"\n串行处理 10 个文档: {serial_time:.2f}s")

# ---- 线程池并发（快）----
start = time.perf_counter()
with ThreadPoolExecutor(max_workers=5) as executor:
    # 方式 1：map（保持顺序，最简洁）
    pool_results = list(executor.map(fetch_embedding, texts))
pool_time = time.perf_counter() - start
print(f"线程池并发（5 worker）: {pool_time:.2f}s")
print(f"加速: {serial_time / pool_time:.1f}x")

# ---- 方式 2：submit + as_completed（不保证顺序，但能获取先完成的）----
print("\nsubmit + as_completed（先完成先处理）:")
start = time.perf_counter()
with ThreadPoolExecutor(max_workers=5) as executor:
    # submit 返回 Future 对象（≈ JS 的 Promise）
    future_to_text = {
        executor.submit(fetch_embedding, text): text
        for text in texts[:5]  # 只取 5 个演示
    }

    # as_completed 按完成顺序迭代（≈ Promise.race 的批量版）
    for future in as_completed(future_to_text):
        text = future_to_text[future]
        try:
            result = future.result()  # ≈ await promise
            print(f"  {text} 完成: embedding={result['embedding']}")
        except Exception as e:
            print(f"  {text} 失败: {e}")


# ============================================================
# 2.3 多进程 —— 绕过 GIL 的终极方案
# ============================================================

print(f"\n{'=' * 60}")
print("2.3 多进程（突破 GIL 限制）")
print("=" * 60)


def cpu_task(n):
    """CPU 密集型任务"""
    return sum(i * i for i in range(n))


# ProcessPoolExecutor（用法和 ThreadPoolExecutor 几乎一样）
if __name__ == "__main__":
    # 注意：Windows 下多进程代码必须在 if __name__ == "__main__" 中

    N = 5_000_000

    # 串行
    start = time.perf_counter()
    cpu_task(N)
    cpu_task(N)
    cpu_task(N)
    cpu_task(N)
    serial_time = time.perf_counter() - start
    print(f"\nCPU 密集串行（4 次）: {serial_time:.3f}s")

    # 多进程
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(cpu_task, N) for _ in range(4)]
        results = [f.result() for f in futures]
    process_time = time.perf_counter() - start
    print(f"CPU 密集多进程（4 worker）: {process_time:.3f}s")
    print(f"加速: {serial_time / process_time:.1f}x")


# ============================================================
# 2.4 线程安全 —— 锁（Lock）
# ============================================================

print(f"\n{'=' * 60}")
print("2.4 线程安全与锁")
print("=" * 60)

# 【面试经典】不加锁的竞态条件
counter_unsafe = 0


def increment_unsafe():
    global counter_unsafe
    for _ in range(100_000):
        counter_unsafe += 1  # 非原子操作！读 → 加 → 写 可能被打断


threads = [threading.Thread(target=increment_unsafe) for _ in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"\n不加锁（期望 500000）: {counter_unsafe}  ← 可能不对！")

# 加锁的正确版本
counter_safe = 0
lock = threading.Lock()


def increment_safe():
    global counter_safe
    for _ in range(100_000):
        with lock:  # ≈ synchronized 块（Java）/ mutex
            counter_safe += 1


threads = [threading.Thread(target=increment_safe) for _ in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"加锁（期望 500000）: {counter_safe}  ← 一定对！")


# ============================================================
# 2.5 选型决策树（面试必问）
# ============================================================

print(f"""
{"=" * 60}
2.5 并发方案选型决策树（面试必背）
{"=" * 60}

你的任务是什么类型？
|
├── I/O 密集（网络请求、文件读写、数据库查询）
|   ├── 需要大量并发（>100）→ asyncio（推荐）
|   |   例：批量调 LLM API、爬虫、WebSocket 服务
|   |
|   └── 并发量不大（<100）→ ThreadPoolExecutor
|       例：并发查数据库、读文件
|
├── CPU 密集（数学计算、数据处理、模型推理）
|   ├── Python 纯代码 → multiprocessing / ProcessPoolExecutor
|   |   例：数据预处理、特征计算
|   |
|   └── 用了 NumPy/Pandas/PyTorch → 它们内部已释放 GIL
|       例：矩阵运算、模型训练（不需要手动多进程）
|
└── 混合型
    → asyncio + ProcessPoolExecutor（异步调度 + 多进程计算）
    例：AI 推理服务（异步接收请求 + 多进程推理）

AI 项目中最常用的组合：
  1. FastAPI（asyncio）接收请求
  2. ThreadPoolExecutor 并发调外部 API
  3. ProcessPoolExecutor 做 CPU 密集的数据处理
""")


# ============================================================
# 2.6 线程间通信：Queue（生产者-消费者模式）
# ============================================================

print("=" * 60)
print("2.6 Queue 生产者-消费者模式")
print("=" * 60)


def producer(q: queue.Queue, items: list):
    """生产者：模拟接收用户请求"""
    for item in items:
        time.sleep(0.02)  # 模拟请求间隔
        q.put(item)
        print(f"  [生产] {item}")
    q.put(None)  # 毒丸信号：告诉消费者结束


def consumer(q: queue.Queue, name: str):
    """消费者：模拟处理请求"""
    while True:
        item = q.get()  # 阻塞等待
        if item is None:
            print(f"  [{name}] 收到结束信号，退出")
            break
        time.sleep(0.05)  # 模拟处理时间
        print(f"  [{name}] 处理完成: {item}")
        q.task_done()


task_queue = queue.Queue(maxsize=5)  # 有界队列，防止内存爆

prod = threading.Thread(target=producer, args=(task_queue, ["请求A", "请求B", "请求C"]))
cons = threading.Thread(target=consumer, args=(task_queue, "Worker-1"))

prod.start()
cons.start()
prod.join()
cons.join()


print(f"\n[OK] Part 2 多线程/多进程/GIL 完成")
