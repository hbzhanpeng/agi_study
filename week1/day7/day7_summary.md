# 第 1 周 Day 7 学习总结：FastAPI + SQLAlchemy 综合实战

> **核心目标：整合前 6 天所学知识，构建一个完整的 CRUD API 项目。**

---

## 1. 项目架构

```
week1/day7/
├── database.py      # 数据库连接配置
├── models.py        # SQLAlchemy 数据模型
├── schemas.py       # Pydantic 数据校验
└── main.py          # FastAPI 应用主文件
```

**架构设计原则**：
- **分层架构**：数据库层、模型层、API 层分离
- **依赖注入**：使用 FastAPI 的 Depends 管理数据库会话
- **类型安全**：Pydantic 自动校验请求数据

---

## 2. 核心知识点

### 2.1 数据库会话管理

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**为什么用 yield？**
- 确保每个请求都有独立的数据库会话
- 请求结束后自动关闭连接，防止连接泄漏

### 2.2 依赖注入模式

```python
@app.post("/todos")
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    # FastAPI 自动注入 db 会话
```

**前端类比**：类似 React 的 useContext / Vue 的 provide/inject

### 2.3 完整的 CRUD 操作

| 操作 | HTTP 方法 | 路径 | 说明 |
|------|----------|------|------|
| Create | POST | /todos | 创建任务 |
| Read | GET | /todos | 查询所有 |
| Read | GET | /todos/{id} | 查询单个 |
| Update | PUT | /todos/{id} | 更新状态 |
| Delete | DELETE | /todos/{id} | 删除任务 |

---

## 3. 面试考点

| 面试问法 | 怎么答 |
|---------|--------|
| "FastAPI 的依赖注入是什么？" | "通过 Depends 自动管理资源生命周期，比如数据库会话。请求开始时创建，结束时自动清理" |
| "为什么要分 schemas 和 models？" | "models 是数据库表结构，schemas 是 API 输入输出格式。分离后可以灵活控制哪些字段暴露给前端" |
| "如何处理 404 错误？" | "查询不到数据时抛出 HTTPException(status_code=404)" |

---

## 4. 下一步测试

运行项目：
```bash
cd week1/day7
uvicorn main:app --reload
```

访问文档：http://localhost:8000/docs

---

**导师寄语**：
> 恭喜完成第 1 周的学习！你已经具备了用 Python 开发后端 API 的基础能力。接下来第 2 周我们会进入 AI/ML 基础概念，这才是 AGI 开发的核心。保持这个节奏！
