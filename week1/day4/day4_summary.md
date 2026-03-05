# 第 1 周 Day 4 学习总结：Python 常用库与环境管理

> **核心目标：掌握真实项目开发中最常用的工具和库，为编写完整的 AI 后端应用打下基础。**

## 1. 虚拟环境与包管理 (Virtual Env & pip)
* **前端类比**：`venv` 类似于前端的每个项目独立的 `node_modules`；`pip` 相当于 `npm/yarn`。
* **为什么需要**：为了隔离不同项目的依赖包版本，避免全局安装导致冲突。
* **核心操作**：
  ```bash
  # 创建名为 .venv 的虚拟环境
  python -m venv .venv
  
  # 激活虚拟环境 (Windows)
  .venv\Scripts\activate
  
  # 安装依赖库
  pip install requests
  
  # 导出当前环境的所有依赖（注意：这会包含传递依赖）
  pip freeze > requirements.txt
  ```
* **面试重点**：能够区分直接依赖和传递依赖。了解现代项目使用 `Poetry` 来精细化锁定依赖（类似于前端的 `package-lock.json` 或 `yarn.lock`）。

## 2. 文件与路径操作 (os & pathlib)
* **前端类比**：Node.js 中的 `path` 和 `fs` 模块。
* **为什么推荐 `pathlib`**：早期使用 `os.path` 操作全是字符串拼接，容易出错且难读。`pathlib` 提供的是面向对象的 `Path` 类，代码极其优雅，更安全且跨平台兼容性更好。
* **核心代码（pathlib 现代写法）**：
  ```python
  from pathlib import Path
  
  # 获取当前目录
  current_path = Path.cwd()
  
  # 优雅拼接路径 (直接用 / )
  log_dir = current_path / "logs"
  log_file = log_dir / "app.log"
  
  # 创建目录 (不存在才创建，包括父目录)
  log_dir.mkdir(parents=True, exist_ok=True)
  
  # 快捷读写文件
  log_file.write_text("System started successfully", encoding="utf-8")
  ```

## 3. 数据处理与类型提示 (json & typing)
* **前端类比**：`json` 对应原生的 `JSON.parse` 和 `JSON.stringify`；`typing` 模块相当于为动态语言 Python 加上了 **TypeScript** 般的类型推断约束。
* **类型提示 (Type Hints)**：
  - 核心作用是：提升开发者体验（IDE代码提示）以及配合静态检查工具拦截错误。
  - **重要概念**：Python 原生的 Type Hints 在运行时**不起作用**。需要配合 `Pydantic` 等库才能在运行时做强校验。
  - 常用类型：`List`, `Dict`, `Optional`, `Any`。
* **核心代码**：
  ```python
  import json
  from typing import Dict, Any

  def parse_llm_response(response_str: str) -> Dict[str, Any]:
      try:
          return json.loads(response_str)
      except json.JSONDecodeError:
          return {}
  ```

## 4. 网络请求 (requests)
* **前端类比**：极其流行的 `axios` 或原生的 `fetch`。
* **核心概念**：被称为 "HTTP for Humans" 的人类友好型库。发送请求时一定要处理超时时间，以及主动暴露非正常状态码。
* **核心代码与防御性编程**：
  ```python
  import requests

  try:
      response = requests.get(
          url="https://api.example.com/data",
          timeout=5 # 面试核心考点：必须加超时时间，防止服务挂死
      )
      # 主动抛出 HTTP 错误 (如果状态码不是 200-299)
      response.raise_for_status() 
      
      data = response.json()
  except requests.exceptions.RequestException as err:
      # RequestException 是 requests 所有异常的基类
      print(f"请求失败: {err}")
  ```

---
**导师寄语**：
> 掌握了这四大模块，你已经具备了独立从外界抓取数据、处理复杂 JSON、并安全写入本地的能力。这也是 AI/大模型调用中最常见的三步曲：**调接口(requests) -> 解析数据(json+typing) -> 存到本地(pathlib)**。保持这个手感，我们继续冲刺下一关！