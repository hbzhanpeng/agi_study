from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

# 创建 FastAPI 实例
app = FastAPI(
    title="AGI 学习助手 API - Part 2",
    description="Level 5-2: Pydantic 数据模型与 POST 请求",
    version="1.0.0"
)

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

# 启动命令提示
if __name__ == "__main__":
    import uvicorn
    print("请在终端运行: uvicorn week1.day5.week1_day5_part2:app --reload")
