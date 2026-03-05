from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_URL = "sqlite:///./agi_study.db"

engine = create_engine(
    BASE_URL, connect_args={"check_same_thread": False}
)

Base = declarative_base()

class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    completed = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

print("数据库表已创建成功！")

Session = sessionmaker(bind=engine)

session = Session()

new_todo = Todo(title="学习 SQLAlchemy", description="完成 Day 6")
session.add(new_todo)
session.commit()
print("新增 Todo 成功！")

all_todos = session.query(Todo).all()
print(all_todos)
for t in all_todos:
    print(t.id, t.title, t.completed)
print("查询所有 Todo 成功！")

todo = session.query(Todo).first()
todo.completed = True
session.commit()
print("更新 Todo 成功！")


session.delete(todo)
session.commit()
print("删除 Todo 成功！")
