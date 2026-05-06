import os

def find_large_files(root_dir, threshold_kb=50):
    print(f"{'文件路径':<60} | {'大小 (KB)':<10}")
    print("-" * 75)
    for root, dirs, files in os.walk(root_dir):
        # 排除已知的干扰项
        if any(x in root for x in ['venv', '.git', '__pycache__', 'chroma_db']):
            continue
        for f in files:
            fp = os.path.join(root, f)
            try:
                size_kb = os.path.getsize(fp) / 1024
                if size_kb > threshold_kb:
                    print(f"{fp:<60} | {size_kb:>8.2f}")
            except:
                pass

# 将路径改为你的实际路径
find_large_files(r'C:\Users\80556\Documents\workSpace\agi-study')