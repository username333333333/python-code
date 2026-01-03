import requests
import json

# 先调用路径计算API获取行程数据
calculate_url = "http://127.0.0.1:5000/path/calculate"
calculate_headers = {"Content-Type": "application/json"}
calculate_body = {
    "start_city": "沈阳", 
    "target_city": "营口", 
    "days": 2, 
    "preferences": {
        "attraction_types": ["博物馆", "公园", "风景区"], 
        "min_rating": 4.0
    }
}

print("正在调用路径计算API...")
calculate_response = requests.post(calculate_url, headers=calculate_headers, json=calculate_body)
if calculate_response.status_code != 200:
    print(f"路径计算API调用失败: {calculate_response.status_code}")
    print(f"错误信息: {calculate_response.text}")
    exit(1)

itinerary_data = calculate_response.json()
if not itinerary_data.get('success'):
    print(f"路径计算失败: {itinerary_data.get('message')}")
    exit(1)

print("路径计算成功！")
print(f"生成了 {len(itinerary_data['itinerary'])} 天的行程")

# 调用地图生成API
map_url = "http://127.0.0.1:5000/path/generate_map"
map_headers = {"Content-Type": "application/json"}
map_body = {
    "itinerary": itinerary_data['itinerary']
}

print("\n正在调用地图生成API...")
map_response = requests.post(map_url, headers=map_headers, json=map_body)
if map_response.status_code != 200:
    print(f"地图生成API调用失败: {map_response.status_code}")
    print(f"错误信息: {map_response.text}")
    exit(1)

map_data = map_response.json()
if not map_data.get('success'):
    print(f"地图生成失败: {map_data.get('message')}")
    exit(1)

print("地图生成成功！")
print("地图HTML长度:", len(map_data['map_html']))

# 将地图HTML保存到文件
with open("test_map.html", "w", encoding="utf-8") as f:
    f.write(map_data['map_html'])

print("\n地图已保存到 test_map.html 文件")
print("你可以在浏览器中打开该文件查看生成的地图")
