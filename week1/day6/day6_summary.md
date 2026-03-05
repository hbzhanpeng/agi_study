# 第 1 周 Day 6 学习总结：SQLAlchemy 数据库操作

> **核心目标：掌握 Python 世界最流行的 ORM 工具，用面向对象的方式操作数据库。**

---

## 1. 为什么需要 ORM？

**真实项目经验**：
- 如果每次查询都手写 SQL，不仅容易出错（SQL 注入风险），而且换数据库（比如从 MySQL 切到 PostgreSQL）时改动巨大
- ORM 把数据库表映射成 Python 类，用面向对象的方式操作数据，代码更优雅，也更安全
- **前端类比**：类似于 Prisma / TypeORM

---

## 2. 核心概念

| 概念 | 作用 |
|------|------|
| **Engine** | 数据库连接引擎，负责连接数据库 |
| **Base** | declarative_base() 的结果，所有模型的基类 |
| **Model (类)** | 对应数据库中的一张表 |
| **Column** | 对应表中的字段 |
| **Session** | 数据库会话，用于增删改查操作 |

---

## 3. CRUD 操作

```python
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. 创建引擎
engine = create_engine("sqlite:///./agi_study.db")

# 2. 创建 Base 和 Model
Base = declarative_base()

class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    completed = Column(Boolean, default=False)

# 3. 建表
Base.metadata.create_all(bind=engine)

# 4. 创建 Session
Session = sessionmaker(bind=engine)
session = Session()

# --- CRUD 操作 ---

# Create（创建）
new_todo = Todo(title="学习 SQLAlchemy")
session.add(new_todo)
session.commit()

# Read（读取）
all_todos = session.query(Todo).all()
todo = session.query(Todo).first()

# Update（更新）
todo.completed = True
session.commit()

# Delete（删除）
session.delete(todo)
session.commit()
```

---

## 4. 面试考点

| 面试问法 | 怎么答 |
|---------|--------|
| "你们用 ORM 还是原生 SQL？" | "主要用 ORM，代码更 Pythonic，切换数据库成本低。复杂查询会用原生 SQL 优化" |
| "ORM 的优缺点是什么？" | "优点：开发快、安全、代码优雅。缺点：有学习成本、复杂查询性能可能不如原生 SQL" |

---

## 5. 工程经验

- **建表时加索引**：`index=True` 可以大幅提升查询速度
- **每次操作后要 commit**：否则数据不会真正保存到数据库
- **用完要关闭 session**（真实项目中通常用 `with` 上下文管理器）

---

**导师寄语**：
> 今天的 CRUD 是所有后端应用的基础。后面我们会把这些操作封装成 API 接口，用户通过 HTTP 请求来操作数据库，这才是完整的 Full Stack 开发流程。继续保持这个节奏！
