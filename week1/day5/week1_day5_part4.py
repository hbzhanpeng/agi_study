from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="AGI 学习助手 API - Part 4",
    description="Level 5-4: To-Do List 综合实战",
    version="1.0.0"
)

# 模拟数据库
db = []

# --- 1. 定义数据模型 ---
# TODO: 请在此处定义你的 Pydantic 模型
# 提示：需要一个用于创建的 TodoCreate 和一个完整的 Todo 模型
class TodoCreate(BaseModel):
    title: str
class Todo(BaseModel):
    id: int
    title: str
    completed: bool = False  # 默认未完成


# --- 2. 实现接口 ---

# GET /todos/ - 获取列表
# TODO: 补充代码
@app.get("/todos/", response_model=List[Todo])
def get_todos():
    return db

# POST /todos/ - 添加
# TODO: 补充代码
@app.post("/todos/", response_model=Todo)
def create_todo(todo_in: TodoCreate):
    # 自动生成 ID
    new_id = len(db) + 1
    # 构造完整 Todo 对象
    new_todo = Todo(
        id=new_id, 
        title=todo_in.title, 
        completed=False
    )
    db.append(new_todo)
    return new_todo

# GET /todos/{todo_id} - 获取详情
# TODO: 补充代码
@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int):
    for todo in db:
        if todo.id == todo_id:
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")

# PUT /todos/{todo_id} - 修改状态
# TODO: 补充代码
@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo: Todo):
    for index, todo in enumerate(db):
        if todo.id == todo_id:
            db[index] = todo
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")

# DELETE /todos/{todo_id} - 删除
# TODO: 补充代码
@app.delete("/todos/{todo_id}", response_model=Todo)
def delete_todo(todo_id: int):
    for index, todo in enumerate(db):
        if todo.id == todo_id:
            deleted_todo = db.pop(index)
            return deleted_todo
    raise HTTPException(status_code=404, detail="Todo not found")

if __name__ == "__main__":
    import uvicorn
    print("请在终端运行: uvicorn week1.day5.week1_day5_part4:app --reload")
