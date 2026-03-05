# 第 1 周 Day 3 学习总结：Python 异步编程与并发控制

> **核心目标：突破 Python 性能瓶颈，学会用异步处理大模型 API 的高延迟调用，理解多线程/多进程的边界。**

## 1. 异步编程 (async/await)
* **前端类比**：非常非常类似 JS 中的 `Promise` 和 `async/await`，底层逻辑几乎一致。
* **为什么 AI 开发必学**：
  - 调用大模型接口（如 GPT-4）动辄几秒到十几秒延迟。如果用同步代码（阻塞型），等待期间服务器就卡死了（类似单线程没开 `async` 的 Node）。
  - 使用 `async/await` 能让你在等待 API 返回的时候去干别的活。
* **核心模块**：必须配合 **`asyncio`** 库（事件循环 Event Loop 引擎）。
* **面试重点（★★★★必考）**：Python 异步 `asyncio.sleep()` 和同步 `time.sleep()` 最大的区别。
* **核心代码**：
  ```python
  import asyncio
  import time
  
  # 定义协程函数
  async def fetch_api(task_id):
      print(f"[{task_id}] 开始调用大模型...")
      await asyncio.sleep(2)  # 模拟 IO 等待 (绝不能用 time.sleep!)
      print(f"[{task_id}] 大模型返回结果！")
      return f"Result-{task_id}"

  # 定义主入口
  async def main():
      start_time = time.time()
      
      # 并发执行多个协程 (类似 JS 的 Promise.all)
      results = await asyncio.gather(
          fetch_api(1),
          fetch_api(2),
          fetch_api(3)
      )
      
      print(f"耗时 {time.time() - start_time:.2f}s, 结果: {results}")

  # 启动事件循环 (Python 3.7+ 标准用法)
  if __name__ == "__main__":
      asyncio.run(main())
  ```

## 2. 多线程 (Threading)
* **前端类比**：JS 里只有 Web Workers 和类似多线程模型。Python 里的多线程是**真·系统线程**。
* **致命缺陷 (GIL 锁)**：
  - Python 因为有 GIL（全局解释器锁），同一时刻只有一个线程能在 CPU 上跑 Python 字节码（假并发）。
  - **面试高频**：Python 多线程适合计算密集型还是 I/O 密集型？
  - **标准答案**：由于 GIL 的存在，**只适合 I/O 密集型**（网络请求、读写文件），CPU 会在这时释放 GIL；**极不适合 CPU 计算密集型**（图像处理、大规模矩阵运算），因为锁竞争反而会拖慢速度。
* **核心代码**：
  ```python
  import threading
  
  def download_task(url):
      print(f"正在下载: {url}")
      
  # 创建线程并启动
  t1 = threading.Thread(target=download_task, args=("http://...",))
  t1.start()
  t1.join() # 等待线程结束 (阻塞主线程)
  ```

## 3. 多进程 (Multiprocessing)
* **前端类比**：类似 Node.js 开启 `cluster` 子进程。
* **解决痛点**：用来绕过 GIL 的终极方案。多进程会把整个 Python 解释器连同数据复制一份给每个核，实现**真正的并行计算**。
* **适用场景**：只适合**计算密集型**（例如用 CPU 洗数据、模型预处理等）。代价是开销非常大，占用海量内存。
* **核心代码**：
  ```python
  from multiprocessing import Process
  
  def compute_heavy_task(data):
      # 执行非常耗时的计算
      pass
      
  if __name__ == "__main__":
      # 必须放在 if __name__ 里，防止 Windows 系统无限递归开子进程
      p = Process(target=compute_heavy_task, args=([1,2,3],))
      p.start()
      p.join()
  ```

---
**导师寄语**：
> 不要把这三者搞混：
> - **网络 I/O 密集型（如并发调 API）**：优先用 `async/await`，开销极小。
> - **无法改造成 async 的老旧 I/O 库**：用多线程 `Threading` 兜底。
> - **耗费 CPU 的纯计算**：用多进程 `Multiprocessing`。
> 拿下异步编程，你在写高并发 AI 智能体 (Agent) 时就不会遇到性能瓶颈了！