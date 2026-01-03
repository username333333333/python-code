import requests
import json

# 测试路径计算API
def test_path_calculate():
    print("测试路径计算API...")
    url = "http://127.0.0.1:5000/path/calculate"
    data = {
        "start_city": "沈阳",
        "target_city": "营口",
        "days": 3,
        "preferences": {
            "attraction_types": ["博物馆", "公园", "风景区"],
            "min_rating": 4.0
        }
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        return response.json()
    except Exception as e:
        print(f"请求失败: {e}")
        return None

# 测试地图生成API
def test_map_generate(itinerary):
    print("\n测试地图生成API...")
    url = "http://127.0.0.1:5000/path/generate_map"
    data = {"itinerary": itinerary}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        return response.json()
    except Exception as e:
        print(f"请求失败: {e}")
        return None

if __name__ == "__main__":
    # 首先测试路径计算
    result = test_path_calculate()
    if result and result.get("success"):
        itinerary = result.get("itinerary")
        if itinerary:
            # 然后测试地图生成
            test_map_generate(itinerary)
