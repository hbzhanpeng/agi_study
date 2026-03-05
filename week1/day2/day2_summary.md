# 第 1 周 Day 2 学习总结：Python 进阶函数与面向对象

> **核心目标：掌握函数的高级玩法，熟悉 Python 的类 (Class) 体系，为写大工程打基础。**

## 1. 闭包与装饰器 (Closures & Decorators)
* **前端类比**：
  * **闭包**：跟 JS 的闭包概念一样，内层函数记住外层函数的局部变量。
  * **装饰器**：极其类似 React 的高阶组件 (HOC)，或者是 TS/Mobx 里的 `@Decorator`。
* **面试考点（★★★必考）**：请手写一个计算函数执行时间的装饰器。
* **为什么重要**：Python 大量 Web 框架（如 FastAPI的 `@app.get`）全靠装饰器驱动。
* **核心代码**：
  ```python
  import time
  
  # 闭包结构：外层接函数，内层写逻辑，返回内层
  def timer_decorator(func):
      def wrapper(*args, **kwargs):
          start = time.time()
          result = func(*args, **kwargs)
          print(f"{func.__name__} 耗时: {time.time() - start:.4f}s")
          return result
      return wrapper
      
  # 使用 @ 语法糖挂载
  @timer_decorator
  def slow_task():
      time.sleep(1)
  ```

## 2. 生成器 (Generators)
* **前端类比**：非常类似 JS 的 `function*` 和 `yield`。
* **核心特征**：它不是一次性把数据都加载到内存（像 List 那样），而是**按需生成，每次 `yield` 一个值**，算完了这轮才进下一轮。
* **面试考点**：列表推导式和生成器表达式的区别？答：中括号 `[]` 是列表（全占内存），小括号 `()` 是生成器（极省内存，适合读取大文件或处理海量 AI 训练数据）。
* **核心代码**：
  ```python
  def count_down(num):
      while num > 0:
          yield num
          num -= 1
          
  # 调用生成器不会立即执行，只返回一个生成器对象
  gen = count_down(3)
  print(next(gen)) # 3
  ```

## 3. 面向对象编程 (OOP)
* **前端类比**：ES6 引入的 `class` 语法。
* **核心差异**：
  1. 构造函数不叫 `constructor`，叫 **`__init__`**（前后双下划线，代表 Python 内部机制所谓的魔术方法）。
  2. 实例方法的第一个参数必须显式声明为 **`self`**，这相当于前端隐式注入的 `this`。如果没有 `self`，方法就找不到上下文。
* **核心代码**：
  ```python
  class AIModel:
      # 构造函数
      def __init__(self, name, version):
          self.name = name  # 类似 this.name
          self.version = version
          
      # 实例方法 (必须带 self)
      def train(self, data):
          print(f"{self.name} v{self.version} is training on {len(data)} items.")

  # 实例化（不需要 new 关键字）
  gpt = AIModel("GPT", "4.0")
  gpt.train([1, 2, 3])
  ```

---
**导师寄语**：
> 装饰器（`@`语法）和生成器（`yield`）是 Python 进阶的分水岭。能熟练手写装饰器，说明你已经摆脱了新手标签，理解了函数作为“一等公民”的灵活运用。