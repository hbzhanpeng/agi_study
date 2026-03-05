from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

app = FastAPI(
    title="AGI 学习助手 API - Part 3",
    description="Level 5-3: 响应模型与错误处理",
    version="1.0.0"
)

# --- 1. 定义数据模型 (Schema) ---

# 输入模型：包含敏感信息 (password)
class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr  # 需要安装 email-validator: pip install email-validator
    full_name: str | None = None

# 输出模型：不包含 password
class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None
    
    # 关键点：即使后端把整个 UserIn 对象传给前端，
    # FastAPI 也会根据 UserOut 的定义自动过滤掉 password

# --- 2. 注册接口 ---
@app.post("/register/", response_model=UserOut)
def register(user: UserIn):
    # 模拟数据库查询：检查用户名是否已存在
    if user.username == "admin":
        # 抛出 HTTP 异常 (类似 Express 的 res.status(400).send(...))
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # 模拟保存到数据库 (这里直接返回输入对象)
    # 注意：这里返回的是包含 password 的 user 对象
    # 但因为装饰器里写了 response_model=UserOut，FastAPI 会自动过滤
    return user

# 启动命令提示
if __name__ == "__main__":
    import uvicorn
    print("请在终端运行: uvicorn week1.day5.week1_day5_part3:app --reload")
