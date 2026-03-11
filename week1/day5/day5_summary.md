# 第 1 周 Day 5 学习总结：FastAPI 后端开发基础

> **核心目标：掌握 FastAPI 核心用法，能独立开发 REST API，理解与 Express 的异同。**

---

## 1. 为什么 AI 项目常用 FastAPI？

```
Flask：老牌框架，同步，性能一般
Django：大而全，太重，AI 项目用不到那么多功能
FastAPI：专为 AI 时代设计
  - 原生 async/await，天然适合 LLM API 的高延迟调用
  - Pydantic 自动校验，省去大量参数验证代码
  - 自动生成 OpenAPI 文档（/docs），前后端联调神器
  - 性能接近 Node.js（基于 Starlette + uvicorn）
```

**面试必答**："FastAPI 为什么快？"
> "基于 Starlette（高性能异步框架）和 Pydantic（C 扩展优化的验证库），全面支持 async/await 非阻塞 I/O，性能接近 Node.js。"

---

## 2. 核心概念对比（前端视角）

| 概念 | FastAPI | Express/Koa | 说明 |
|------|---------|-------------|------|
| 路由装饰器 | `@app.get("/")` | `app.get("/", fn)` | Python 用装饰器注册路由 |
| 类型校验 | `Pydantic` | `Zod / Joi` | 运行时数据验证 + 自动转换 |
| API 文档 | 自动生成 `/docs` | 手写 Swagger | 基于类型注解自动生成 |
| 热重载 | `uvicorn --reload` | `nodemon` | 开发时自动重启 |
| 中间件 | `@app.middleware` | `app.use()` | 请求/响应拦截 |

---

## 3. 路由与参数

### 路径参数 vs 查询参数

```python
from fastapi import FastAPI

app = FastAPI()

# 路径参数：/items/42
@app.get("/items/{item_id}")
def get_item(item_id: int):   # 自动把字符串 "42" 转成 int 42
    return {"id": item_id}

# 查询参数：/items?skip=0&limit=10
@app.get("/items")
def list_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

# 混合：/users/42/orders?status=pending
@app.get("/users/{user_id}/orders")
def get_orders(user_id: int, status: str = "all"):
    return {"user_id": user_id, "status": status}
```

**规律**：函数参数在路径里 → 路径参数；不在路径里 → 自动识别为查询参数。

---

## 4. Pydantic 数据模型

**前端类比**：Pydantic = Python 版的 Zod/Yup，但更强大——它不只是验证，还会**自动类型转换**。

```python
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: str
    age: int
    bio: Optional[str] = None   # 可选字段，默认 None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    # 注意：没有 password 字段！

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate):
    # FastAPI 自动：
    # 1. 读取请求体 JSON
    # 2. 校验字段类型
    # 3. 转换类型（如字符串 "25" → int 25）
    # 4. 返回时只包含 UserResponse 里的字段（自动过滤 password）
    new_user = save_to_db(user)
    return new_user
```

**核心价值**：
- `response_model` 自动过滤敏感字段（如 password）
- 请求体自动校验，类型错误返回 422，不需要手写 if 判断
- 自动生成 API 文档，前端直接看 `/docs`

---

## 5. 错误处理

```python
from fastapi import HTTPException

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = db.get(user_id)

    if not user:
        # 类似 Express 的 res.status(404).json({detail: "..."})
        raise HTTPException(
            status_code=404,
            detail=f"用户 {user_id} 不存在"
        )

    return user
```

**全局异常处理**（类似 Express 的 error middleware）：

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "error": str(exc)}
    )
```

---

## 6. 依赖注入（Depends）

**前端类比**：类似 React 的 Context，把公共依赖（数据库连接、当前用户）注入到路由函数。

```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db   # yield 让 FastAPI 在请求结束后自动关闭连接
    finally:
        db.close()

def get_current_user(token: str, db = Depends(get_db)):
    user = db.query(User).filter(User.token == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    return user

# 路由自动注入当前用户
@app.get("/profile")
def get_profile(current_user = Depends(get_current_user)):
    return current_user
```

**为什么用 Depends**：
- 复用逻辑（多个路由共用同一个权限校验）
- 自动管理资源生命周期（数据库连接自动关闭）
- 测试时可以轻松替换（mock 依赖）

---

## 7. RESTful CRUD 最佳实践

```python
# 标准 RESTful 路由设计
@app.get("/items")           # 列表
@app.post("/items")          # 创建
@app.get("/items/{id}")      # 详情
@app.put("/items/{id}")      # 全量更新
@app.patch("/items/{id}")    # 部分更新
@app.delete("/items/{id}")   # 删除

# Pydantic 模型拆分（最佳实践）
class ItemBase(BaseModel):
    name: str
    price: float

class ItemCreate(ItemBase):
    pass   # 创建时不需要 id

class ItemUpdate(BaseModel):
    name: Optional[str] = None    # 部分更新，所有字段可选
    price: Optional[float] = None

class ItemResponse(ItemBase):
    id: int                       # 响应时包含 id
    class Config:
        from_attributes = True    # 支持从 ORM 对象转换
```

---

## 8. 面试考点汇总

### 问法 1："FastAPI 和 Flask/Django 的区别？"

**标准答案**：
> "FastAPI 原生支持 async/await，性能接近 Node.js，适合 AI 应用的高并发场景。Flask 是同步框架，性能较低。Django 大而全但太重，AI 项目用不到那么多功能。FastAPI 还有自动生成 API 文档、Pydantic 自动校验等特性，开发效率更高。"

### 问法 2："Pydantic 和普通 Python 类有什么区别？"

**标准答案**：
> "Pydantic 是解析库而非验证库：它会尝试把输入数据转换成目标类型（如字符串 '123' 转 int 123），而不只是检查类型。还支持嵌套模型、自定义验证器、JSON 序列化等。FastAPI 用 Pydantic 自动处理请求体校验和响应序列化。"

### 问法 3："FastAPI 的依赖注入有什么用？"

**标准答案**：
> "Depends 用于复用公共逻辑，如数据库连接、权限校验、参数解析。它支持 yield 语法自动管理资源生命周期（如数据库连接用完自动关闭）。测试时可以轻松替换依赖（override），不需要 mock 整个模块。"

**加分项**：
- 能说出 `response_model` 自动过滤敏感字段的原理
- 能说出 `async def` vs `def` 路由的区别（I/O 密集用 async）

---

## 9. 真实踩坑经历

**坑 1：忘记用 async def 导致阻塞**
> 调用 LLM API 时用了普通 `def`，结果并发请求时全部排队等待，QPS 极低。改成 `async def` + `await` 后，并发性能提升 10 倍。

**坑 2：response_model 没设置导致密码泄露**
> 早期没有设置 `response_model`，直接 `return user`，结果把数据库里的 `hashed_password` 字段也返回给前端了。加了 `response_model=UserResponse`（不含 password 字段）后解决。

**坑 3：Pydantic v1 和 v2 不兼容**
> 升级 FastAPI 后，`orm_mode = True` 改成了 `from_attributes = True`，导致所有 ORM 模型转换报错。升级时一定要看 migration guide。

---

**导师寄语**：
> FastAPI 是 AI 应用开发的标配框架，面试官问这个是想看你有没有真正写过后端 API。记住三个核心：async/await 处理高延迟、Pydantic 自动校验、Depends 复用逻辑。这三个点能聊清楚，FastAPI 这关就过了。

**下一步**：Week1 Day6 — SQLAlchemy ORM 数据库操作
