import requests
from typing import Dict, Any

print("--- 发送 HTTP 请求 ---")

try:
    response = requests.get(
        url = "https://api.github.com/users/octocat",
        params = {"per_page": 1},
        timeout = 5
    )
    response.raise_for_status()
    user_info: Dict[str, Any] = response.json()
    print(f"用户信息: {user_info}")
    print(f"获取到用户: {user_info.get("login")}, Id: {user_info.get("id")}")
except requests.exceptions.HTTPError as errh:
    print(f"HTTP 错误: {errh}")
except requests.exceptions.ConnectionError as errc:
    print(f"连接错误: {errc}")
except requests.exceptions.Timeout as errt:
    print(f"超时错误: {errt}")
except requests.exceptions.RequestException as err:
    print(f"其他错误: {err}")


print("\n--- 2. 发送 POST 请求 ---")
# 类似于 axios.post('url', data, { headers: { ... } })
url = "https://httpbin.org/post" # 这是一个专门用来测试 HTTP 请求的网站
payload = {"name": "AGI Learner", "role": "Developer"}
headers = {
    "User-Agent": "My-Python-App/1.0",
    "Authorization": "Bearer fake_token_123"
}
try:
    response = requests.post(
        url = url,
        json = payload,
        headers = headers,
        timeout = 5
    )
    response.raise_for_status()
    print(f"POST 请求成功, 响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
except requests.exceptions.RequestException as err:
    print(f"Post 请求失败: {err}")


from pathlib import Path
import json
def fetch_and_save_todo(todo_id: int):
    try:
        response = requests.get(
            url = f"https://jsonplaceholder.typicode.com/todos/{todo_id}",
            timeout = 5
        )
        response.raise_for_status()
        todo_data = response.json()
        print(f"响应内容: {todo_data}")
        current_dir = Path.cwd()
        print(f"当前目录: {current_dir}")
        todo_file = current_dir / f"todo_{todo_id}.json"
        todo_file.write_text(json.dumps(todo_data, indent=2, ensure_ascii=False))
    except requests.exceptions.RequestException as err:
        print(f"获取 Todo {todo_id} 失败: {err}")

fetch_and_save_todo(1)