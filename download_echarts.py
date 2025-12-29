import requests
import os

url = "https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"
file_path = "echarts.min.js"

proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}

try:
    print(f"正在下载 {url} (使用代理)...")
    response = requests.get(url, proxies=proxies, timeout=30)
    if response.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"下载成功: {os.path.abspath(file_path)}")
    else:
        print(f"下载失败: {response.status_code}")
except Exception as e:
    print(f"发生错误: {e}")
