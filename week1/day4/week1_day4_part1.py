import os
from pathlib import Path

# --- 传统做法 (os 模块) ---
print("--- os.path 传统方式 ---")
# 获取当前目录
current_dir_os = os.getcwd()
print(f"当前目录: {current_dir_os}")

# 拼接路径: /当前目录/data/config.json
config_path_os = os.path.join(current_dir_os, "data", "config.json")
print(f"配置文件路径: {config_path_os}")
# 获取文件名和后缀
file_name = os.path.basename(config_path_os)
dir_name = os.path.dirname(config_path_os)
print(f"目录名: {dir_name}, 文件名: {file_name}")
# 创建目录 (如果不存在)
# os.makedirs(os.path.join(current_dir_os, "data"), exist_ok=True)
# --- 现代做法 (pathlib 模块) 推荐！ ---
print("\n--- pathlib 现代方式 ---")
# 获取当前工作目录
current_path = Path.cwd()
print(f"当前目录: {current_path}")
# 极其优雅的路径拼接！直接用 / 操作符
config_path = current_path / "data" / "config.json"
print(f"配置文件路径: {config_path}")
# 对象属性直接获取信息，清晰明了
print(f"目录名: {config_path.parent}")
print(f"文件名: {config_path.name}")
print(f"文件后缀: {config_path.suffix}")
print(f"是否是文件?: {config_path.is_file()}")
print(f"文件是否存在?: {config_path.exists()}")
# 创建目录及其父目录
data_dir = current_path / "data"
data_dir.mkdir(parents=True, exist_ok=True) # 类似 mkdir -p，不存在才创建
# pathlib 还能一键读写文件，不需要麻烦的 with open()
test_file = data_dir / "test.txt"
test_file.write_text("Hello AGI World!", encoding="utf-8")
print(f"文件内容读取: {test_file.read_text(encoding='utf-8')}")


current_path = Path.cwd()
log_dir = current_path / "logs"
log_dir.mkdir(parents=True, exist_ok = True)

test_log = log_dir / "app.log"
test_log.write_text("System started successfully", encoding="utf-8")
