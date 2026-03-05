# ============================================================
# 第 1 周 Day 3 - Part 1：async/await 基础
# ============================================================
#
# 前端类比对照表（核心认知转换）：
#
# | JS                        | Python                      |
# |---------------------------|-----------------------------|
# | Promise                   | Coroutine（协程）            |
# | async function            | async def                   |
# | await promise             | await coroutine             |
# | Promise.all([...])        | asyncio.gather(...)         |
# | Promise.race([...])       | asyncio.wait(..., FIRST_COMPLETED) |
# | setTimeout(fn, ms)        | asyncio.sleep(s)            |
# | fetch()                   | aiohttp.get()               |
# | 事件循环（V8 自动管理）     | asyncio.run()（需要手动启动）|
#
# 【关键区别】
# JS：浏览器/Node 自带事件循环，async 函数直接调用就能跑
# Python：没有内置的运行中事件循环，必须用 asyncio.run() 启动
# ============================================================

import asyncio
import time


# ============================================================
# 1.1 最基础的协程
# ============================================================

# JS 版本：
# async function greet(name) {
#     await new Promise(r => setTimeout(r, 1000));
#     return `Hello ${name}`;
# }
# greet("AI").then(console.log);


# Python 版本：
async def greet(name: str) -> str:
    """最简单的协程函数"""
    await asyncio.sleep(0.1)  # ≈ JS 的 await new Promise(r => setTimeout(r, 100))
    return f"Hello {name}"


async def demo_basic():
    print("--- 1.1 基础协程 ---")

    # 调用协程必须 await（和 JS 一样）
    result = await greet("AGI")
    print(f"  result = {result}")

    # 【面试考点】直接调用协程函数不会执行！只会返回一个协程对象
    coro = greet("World")  # 没有 await，不会执行
    print(f"  未 await 的协程对象: {coro}")
    print(f"  类型: {type(coro)}")
    # 需要 await 才会真正执行
    result2 = await coro
    print(f"  await 后: {result2}")


# ============================================================
# 1.2 并发执行：asyncio.gather ≈ Promise.all
# ============================================================


async def fetch_model_response(model_name: str, delay: float) -> dict:
    """模拟调用不同的 LLM API（每个模型响应时间不同）"""
    print(f"  [{model_name}] 开始请求...")
    await asyncio.sleep(delay)  # 模拟网络延迟
    print(f"  [{model_name}] 响应完成（{delay}s）")
    return {
        "model": model_name,
        "response": f"{model_name} says hello",
        "latency": delay,
    }


async def demo_gather():
    print("\n--- 1.2 asyncio.gather（并发请求） ---")

    # 串行调用（慢！）
    start = time.perf_counter()
    r1 = await fetch_model_response("GPT-4", 0.3)
    r2 = await fetch_model_response("Claude", 0.2)
    r3 = await fetch_model_response("Gemini", 0.1)
    serial_time = time.perf_counter() - start
    print(f"  串行耗时: {serial_time:.2f}s（0.3+0.2+0.1=0.6s）\n")

    # 并发调用（快！）≈ Promise.all
    start = time.perf_counter()
    results = await asyncio.gather(
        fetch_model_response("GPT-4", 0.3),
        fetch_model_response("Claude", 0.2),
        fetch_model_response("Gemini", 0.1),
    )
    concurrent_time = time.perf_counter() - start
    print(f"  并发耗时: {concurrent_time:.2f}s（≈ max(0.3,0.2,0.1)=0.3s）")
    print(f"  提速: {serial_time / concurrent_time:.1f}x")

    for r in results:
        print(f"    {r['model']}: {r['response']}")


# ============================================================
# 1.3 错误处理：return_exceptions 参数
# ============================================================


async def risky_api_call(name: str, should_fail: bool = False):
    """模拟可能失败的 API 调用"""
    await asyncio.sleep(0.05)
    if should_fail:
        raise ConnectionError(f"{name} 连接失败")
    return f"{name} 成功"


async def demo_error_handling():
    print("\n--- 1.3 并发错误处理 ---")

    # 方式 1：return_exceptions=False（默认，一个失败全部失败）
    # ≈ Promise.all 的行为：任何一个 reject 就整体 reject
    print("  方式 1: return_exceptions=False（默认）")
    try:
        results = await asyncio.gather(
            risky_api_call("A"),
            risky_api_call("B", should_fail=True),
            risky_api_call("C"),
        )
    except ConnectionError as e:
        print(f"    整体失败: {e}")

    # 方式 2：return_exceptions=True（异常作为返回值，不中断其他任务）
    # ≈ Promise.allSettled 的行为
    print("  方式 2: return_exceptions=True（≈ Promise.allSettled）")
    results = await asyncio.gather(
        risky_api_call("A"),
        risky_api_call("B", should_fail=True),
        risky_api_call("C"),
        return_exceptions=True,  # 异常不会抛出，而是作为结果返回
    )
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            print(f"    任务 {i}: 失败 - {r}")
        else:
            print(f"    任务 {i}: 成功 - {r}")


# ============================================================
# 1.4 超时控制：asyncio.wait_for ≈ Promise.race + timeout
# ============================================================


async def slow_llm_call():
    """模拟一个很慢的模型调用"""
    await asyncio.sleep(5)  # 5 秒
    return "终于完成了"


async def demo_timeout():
    print("\n--- 1.4 超时控制 ---")

    # 设置超时（AI 项目中调 LLM API 必须设超时）
    try:
        result = await asyncio.wait_for(
            slow_llm_call(),
            timeout=0.5,  # 500ms 超时
        )
    except asyncio.TimeoutError:
        print("  模型调用超时（500ms），启用降级策略")
        # 实际项目中：切换到更快的模型 / 返回缓存结果 / 报错


# ============================================================
# 1.5 创建和管理 Task
# ============================================================


async def background_job(name: str, duration: float):
    """后台任务"""
    await asyncio.sleep(duration)
    return f"{name} 完成"


async def demo_tasks():
    print("\n--- 1.5 Task 管理 ---")

    # 创建 Task（≈ 不 await 的 Promise，让它在后台跑）
    task1 = asyncio.create_task(background_job("索引构建", 0.3))
    task2 = asyncio.create_task(background_job("模型预热", 0.2))

    print("  任务已创建，继续做其他事...")
    await asyncio.sleep(0.1)
    print("  做了 100ms 其他工作")

    # 等待所有 task 完成
    result1 = await task1
    result2 = await task2
    print(f"  {result1}, {result2}")

    # Task 取消（≈ AbortController.abort()）
    task3 = asyncio.create_task(background_job("大任务", 10))
    await asyncio.sleep(0.05)
    task3.cancel()  # 取消任务
    try:
        await task3
    except asyncio.CancelledError:
        print("  大任务已被取消")


# ============================================================
# 1.6 异步迭代器（async for）—— 流式读取 LLM 响应
# ============================================================


async def stream_tokens(text: str, delay: float = 0.02):
    """
    异步生成器：模拟 LLM 流式输出

    ≈ JS 的 async function*
    真实场景：OpenAI API stream=True 返回的就是这种异步迭代器
    """
    for word in text.split():
        await asyncio.sleep(delay)  # 模拟模型推理延迟
        yield word


async def demo_async_iter():
    print("\n--- 1.6 异步迭代器（async for）---")

    print("  AI: ", end="", flush=True)
    # async for ≈ JS 的 for await...of
    async for token in stream_tokens("AGI will transform how we build software"):
        print(token, end=" ", flush=True)
    print()


# ============================================================
# 1.7 信号量（Semaphore）—— 控制并发数
# ============================================================


async def call_api_with_id(api_id: int, semaphore: asyncio.Semaphore):
    """受信号量控制的 API 调用"""
    async with semaphore:  # 获取许可（超过限制则等待）
        print(f"    API-{api_id} 开始（并发槽位已占用）")
        await asyncio.sleep(0.1)
        print(f"    API-{api_id} 完成（释放槽位）")
        return f"result-{api_id}"


async def demo_semaphore():
    print("\n--- 1.7 信号量控制并发数 ---")
    print("  场景：OpenAI API 限制每秒 5 个并发请求")

    # 最多同时 3 个并发（模拟 API 并发限制）
    semaphore = asyncio.Semaphore(3)

    # 发起 6 个请求，但最多同时跑 3 个
    tasks = [call_api_with_id(i, semaphore) for i in range(6)]
    results = await asyncio.gather(*tasks)
    print(f"  全部完成: {results}")


# ============================================================
# 运行所有演示
# ============================================================


async def main():
    await demo_basic()
    await demo_gather()
    await demo_error_handling()
    await demo_timeout()
    await demo_tasks()
    await demo_async_iter()
    await demo_semaphore()
    print("\n[OK] Part 1 async/await 完成")


# 启动事件循环（JS 不需要这步，Python 必须手动启动）
asyncio.run(main())
