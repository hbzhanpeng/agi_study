# Day 5 学习总结：FastAPI 后端开发基础

## 1. 核心概念对比 (前端视角)

| 概念 | FastAPI (Python) | Express/Koa (Node.js) | 说明 |
| :--- | :--- | :--- | :--- |
| **Web 框架** | `FastAPI` | `Express` | 提供路由、中间件、请求处理 |
| **类型校验** | `Pydantic` | `Zod` / `Joi` | 运行时数据结构验证 + 自动转换 |
| **API 文档** | 自动生成 (`/docs`) | 手写 Swagger | FastAPI 基于类型提示自动生成 OpenAPI |
| **热重载** | `uvicorn --reload` | `nodemon` | 开发时修改代码自动重启服务 |
| **装饰器路由** | `@app.get("/")` | `app.get("/", ...)` | Python 使用装饰器注册路由 |

## 2. 关键知识点

### 2.1 路由与参数
- **路径参数**：`@app.get("/items/{item_id}")`，函数参数 `item_id: int` 会自动转换类型。
- **查询参数**：函数参数未在路径中声明时（如 `skip: int = 0`），自动识别为 Query 参数（`?skip=0`）。

### 2.2 Pydantic 数据模型 (Schema)
- **定义**：继承 `BaseModel`，使用 Python 类型注解。
- **输入校验**：作为请求体参数（`item: Item`），FastAPI 会自动读取 JSON 并校验。
- **输出过滤**：`response_model=UserOut`，自动剔除敏感字段（如 `password`）。

```python
class UserIn(BaseModel):
    username: str
    password: str  # 敏感信息

class UserOut(BaseModel):
    username: str
    # 不包含 password

@app.post("/register/", response_model=UserOut)
def register(user: UserIn):
    return user  # 返回包含 password 的对象，但前端只会收到 UserOut 里的字段
```

### 2.3 错误处理
- 使用 `HTTPException` 抛出 HTTP 错误，中断执行。
- 类似 Express 的 `res.status(404).send(...)`。

```python
from fastapi import HTTPException
raise HTTPException(status_code=404, detail="Item not found")
```

### 2.4 CRUD 最佳实践
- **模型拆分**：`Create` 模型（无 ID）vs 完整模型（有 ID）。
- **RESTful 规范**：
  - `GET /resource` (列表)
  - `POST /resource` (创建)
  - `GET /resource/{id}` (详情)
  - `PUT /resource/{id}` (全量替换)
  - `DELETE /resource/{id}` (删除)

## 3. 今日代码结构

- `week1_day5_part1.py`: FastAPI 初体验（路由、路径参数）
- `week1_day5_part2.py`: Pydantic 数据模型与 POST 请求
- `week1_day5_part3.py`: 响应模型与错误处理（Response Model）
- `week1_day5_part4.py`: **[实战]** 内存版 To-Do List CRUD API

## 4. 面试必考题

1. **FastAPI 为什么快？**
   - 基于 `Starlette`（高性能异步框架）和 `Pydantic`（C 语言扩展优化的验证库）。
   - 全面支持 `async/await`，非阻塞 I/O。

2. **Pydantic 和普通 Python 类有什么区别？**
   - Pydantic 是**解析库**而非验证库：它会尝试把输入数据**转换**成目标类型（如字符串 "123" 转 int 123），而不仅仅是检查类型。

3. **如何处理 FastAPI 的依赖注入？**
   - 使用 `Depends`（明天 Day 6 会讲，常用于数据库连接、权限验证）。
