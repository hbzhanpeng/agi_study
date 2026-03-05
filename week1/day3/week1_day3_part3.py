# ============================================================
# 第 1 周 Day 3 - Part 3：综合实战 —— AI 批量推理引擎
# ============================================================
#
# 目标：用 asyncio + Semaphore + 重试 构建一个生产级的
#       批量 LLM API 调用框架
#
# 这就是你面试时可以讲的项目经验：
# "我设计了一个支持并发限流、自动重试、流式输出的 LLM 调用框架"
# ============================================================

import asyncio
import time
import random
from dataclasses import dataclass, field
from typing import Optional
from functools import wraps


# ============================================================
# 3.1 数据模型（用 dataclass，≈ TS 的 interface）
# ============================================================


@dataclass
class LLMRequest:
    """LLM 请求"""

    prompt: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1000
    request_id: int = 0


@dataclass
class LLMResponse:
    """LLM 响应"""

    request_id: int
    content: str
    model: str
    latency: float
    success: bool = True
    error: Optional[str] = None


# ============================================================
# 3.2 模拟 LLM API（带随机延迟和失败率）
# ============================================================


async def fake_llm_api(request: LLMRequest) -> str:
    """
    模拟 OpenAI API 调用
    - 随机延迟 50-200ms（模拟网络 + 推理时间）
    - 15% 概率失败（模拟网络不稳定 / 限流）
    """
    delay = random.uniform(0.05, 0.2)
    await asyncio.sleep(delay)

    # 模拟随机失败
    if random.random() < 0.15:
        error_type = random.choice(["RateLimitError", "TimeoutError", "ServerError"])
        raise ConnectionError(f"{error_type}: API 调用失败")

    return f"[{request.model}] 回答 #{request.request_id}: 这是关于'{request.prompt}'的回复"


# ============================================================
# 3.3 重试装饰器（异步版本 —— Day2 装饰器的 async 升级）
# ============================================================


def async_retry(max_retries=3, base_delay=0.1, exponential=True):
    """
    异步重试装饰器 + 指数退避

    exponential=True 时：
    第 1 次重试等 0.1s，第 2 次等 0.2s，第 3 次等 0.4s

    这是调外部 API 的标准做法（面试必知）
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = (
                            base_delay * (2 ** (attempt - 1))
                            if exponential
                            else base_delay
                        )
                        # 加随机抖动避免惊群效应（面试加分点）
                        jitter = random.uniform(0, delay * 0.1)
                        await asyncio.sleep(delay + jitter)
            raise last_error

        return wrapper

    return decorator


# ============================================================
# 3.4 批量推理引擎（核心）
# ============================================================


class BatchInferenceEngine:
    """
    批量 LLM 推理引擎

    特性：
    1. Semaphore 控制并发数（不超过 API 限制）
    2. 自动重试 + 指数退避
    3. 实时进度报告
    4. 错误收集（不因单个失败中断全部）

    面试中这样讲：
    "我设计了一个生产级的批量推理引擎，支持并发限流、
     指数退避重试、错误隔离，能稳定处理上千个请求"
    """

    def __init__(self, max_concurrent: int = 10, max_retries: int = 3):
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # 统计指标
        self.total = 0
        self.completed = 0
        self.failed = 0
        self.start_time = 0

    @async_retry(max_retries=3, base_delay=0.05)
    async def _call_api(self, request: LLMRequest) -> str:
        """带重试的单次 API 调用"""
        return await fake_llm_api(request)

    async def _process_single(self, request: LLMRequest) -> LLMResponse:
        """处理单个请求（带并发控制）"""
        async with self.semaphore:  # 并发限流
            start = time.perf_counter()
            try:
                content = await self._call_api(request)
                latency = time.perf_counter() - start
                self.completed += 1
                return LLMResponse(
                    request_id=request.request_id,
                    content=content,
                    model=request.model,
                    latency=latency,
                    success=True,
                )
            except Exception as e:
                latency = time.perf_counter() - start
                self.failed += 1
                return LLMResponse(
                    request_id=request.request_id,
                    content="",
                    model=request.model,
                    latency=latency,
                    success=False,
                    error=str(e),
                )
            finally:
                # 进度报告
                done = self.completed + self.failed
                if done % 5 == 0 or done == self.total:
                    elapsed = time.perf_counter() - self.start_time
                    qps = done / elapsed if elapsed > 0 else 0
                    print(
                        f"  进度: {done}/{self.total} "
                        f"(成功:{self.completed} 失败:{self.failed}) "
                        f"QPS:{qps:.1f}"
                    )

    async def run(self, requests: list[LLMRequest]) -> list[LLMResponse]:
        """
        批量执行所有请求

        用 asyncio.gather + return_exceptions=False
        （我们在 _process_single 里已经 catch 了异常，不会中断）
        """
        self.total = len(requests)
        self.completed = 0
        self.failed = 0
        self.start_time = time.perf_counter()

        print(f"\n  开始批量推理: {self.total} 个请求, 并发上限: {self.max_concurrent}")

        # 并发执行所有请求
        tasks = [self._process_single(req) for req in requests]
        results = await asyncio.gather(*tasks)

        # 统计报告
        total_time = time.perf_counter() - self.start_time
        avg_latency = sum(r.latency for r in results) / len(results)

        print(f"\n  === 批量推理完成 ===")
        print(f"  总耗时: {total_time:.2f}s")
        print(f"  成功: {self.completed}/{self.total}")
        print(f"  失败: {self.failed}/{self.total}")
        print(f"  平均延迟: {avg_latency:.3f}s")
        print(f"  吞吐量: {self.total / total_time:.1f} req/s")

        return results


# ============================================================
# 3.5 异步生产者-消费者模式（进阶）
# ============================================================


async def async_producer_consumer_demo():
    """
    异步版生产者-消费者

    场景：用户请求不断进来（生产者），
         后台 worker 持续处理（消费者）

    ≈ Node.js 的消息队列模式
    """
    print(f"\n{'=' * 60}")
    print("3.5 异步生产者-消费者模式")
    print("=" * 60)

    # asyncio.Queue ≈ 异步版的 queue.Queue
    task_queue: asyncio.Queue = asyncio.Queue(maxsize=10)
    results = []

    async def producer():
        """模拟用户不断发来请求"""
        for i in range(8):
            request = LLMRequest(prompt=f"问题{i}", request_id=i)
            await task_queue.put(request)  # 队列满时会等待
            print(f"    [生产] 请求 #{i} 入队")
            await asyncio.sleep(0.02)  # 模拟请求间隔

        # 发送结束信号（放入 None）
        await task_queue.put(None)
        await task_queue.put(None)  # 两个消费者就放两个

    async def consumer(name: str):
        """消费者 worker"""
        while True:
            request = await task_queue.get()  # 阻塞等待
            if request is None:
                print(f"    [{name}] 收到结束信号")
                break

            # 处理请求
            await asyncio.sleep(0.05)  # 模拟处理时间
            result = f"{name} 处理了请求 #{request.request_id}"
            results.append(result)
            print(f"    [{name}] {result}")
            task_queue.task_done()

    # 启动 1 个生产者 + 2 个消费者
    await asyncio.gather(
        producer(),
        consumer("Worker-A"),
        consumer("Worker-B"),
    )

    print(f"  共处理 {len(results)} 个请求")


# ============================================================
# 3.6 asyncio + ThreadPoolExecutor 混合模式
# ============================================================

import concurrent.futures


async def hybrid_demo():
    """
    混合模式：asyncio 调度 + 线程池执行同步代码

    场景：你需要调用一个不支持 async 的库（如某些数据库驱动）
    用 loop.run_in_executor() 把同步函数放到线程池执行

    ≈ Node.js 的 worker_threads 处理 CPU 密集任务
    """
    print(f"\n{'=' * 60}")
    print("3.6 asyncio + ThreadPoolExecutor 混合模式")
    print("=" * 60)

    def sync_heavy_computation(n: int) -> int:
        """同步的 CPU 密集函数（不能用 await）"""
        return sum(i * i for i in range(n))

    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    # 把同步函数包装成异步调用
    start = time.perf_counter()

    # 并发执行 4 个 CPU 任务（通过线程池）
    tasks = [
        loop.run_in_executor(executor, sync_heavy_computation, 1_000_000)
        for _ in range(4)
    ]
    results = await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - start
    print(f"  4 个计算任务并发完成: {elapsed:.3f}s")
    print(f"  结果: {[r for r in results]}")

    executor.shutdown(wait=False)


# ============================================================
# 运行
# ============================================================


async def main():
    random.seed(42)

    # 演示 1：批量推理引擎
    print("=" * 60)
    print("3.4 批量推理引擎演示")
    print("=" * 60)

    engine = BatchInferenceEngine(max_concurrent=5, max_retries=3)

    # 创建 20 个请求
    requests = [
        LLMRequest(
            prompt=f"什么是 AGI 的第 {i} 个特点？",
            model="gpt-4",
            request_id=i,
        )
        for i in range(20)
    ]

    results = await engine.run(requests)

    # 展示部分结果
    print("\n  前 3 个成功的结果:")
    success_results = [r for r in results if r.success]
    for r in success_results[:3]:
        print(f"    #{r.request_id}: {r.content[:50]}... ({r.latency:.3f}s)")

    # 展示失败的
    failed_results = [r for r in results if not r.success]
    if failed_results:
        print(f"\n  失败的请求 ({len(failed_results)} 个):")
        for r in failed_results[:3]:
            print(f"    #{r.request_id}: {r.error}")

    # 演示 2：生产者-消费者
    await async_producer_consumer_demo()

    # 演示 3：混合模式
    await hybrid_demo()

    print(f"\n[OK] Part 3 综合实战 完成")


asyncio.run(main())
