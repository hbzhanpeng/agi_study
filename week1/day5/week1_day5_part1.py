from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

# 创建 FastAPI 实例 (类似前端的 const app = express())
app = FastAPI(
    title="AGI 学习助手 API",
    description="这是一个专门用来学习大模型开发的 API",
    version="1.0.0"
)

# 定义根路由 (类似 app.get('/', (req, res) => ...))
@app.get("/")
def read_root():
    return {"message": "Welcome to AGI API!", "status": "online"}

# 定义一个带路径参数的接口
@app.get("/hello/{name}")
def greet(name: str):
    return {"greeting": f"Hello, {name}!", "your_name": name}

@app.get("/users/{user_id}/items/{item_id}")
def read_user_item(user_id: int, item_id: str):
    return {"user": user_id, "item": item_id, "description": "User's item"}


# --- 1. 定义数据模型 (Schema) ---
# 类比 TS interface:
# interface Item {
#   name: string;
#   price: number;
#   is_offer?: boolean;
# }
class Item(BaseModel):
    name: str
    price: float
    is_offer: Optional[bool] = None  # 可选字段，默认 None
# --- 2. 新增 POST 接口 ---
# 自动校验：如果请求体 JSON 不符合 Item 结构，直接返回 422 错误
@app.post("/items/")
def create_item(item: Item):
    # item 已经是验证过的 Item 对象，可直接访问属性
    result = {"item_name": item.name, "item_price": item.price}
    
    # 业务逻辑：如果有折扣，加个字段
    if item.is_offer:
        result.update({"discount": "10% off"})
        
    return result
