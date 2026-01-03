import requests
import os

# 保存路径（你的 static/js 目录）
save_path = os.path.join("static", "js", "liaoning.json")

# 辽宁省 GeoJSON 数据 URL（高德地图或阿里 CDN 上的可用版本）
url = "https://geo.datav.aliyun.com/areas/bound/210000_full.json"  # 210000 = 辽宁省

try:
    response = requests.get(url)
    response.raise_for_status()
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"✅ 下载成功，已保存至 {save_path}")
except Exception as e:
    print(f"❌ 下载失败: {e}")
