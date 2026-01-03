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
        result = response.json()
        
        if result and result.get("success"):
            itinerary = result.get("itinerary")
            if itinerary:
                print("\n行程中的景点及城市:")
                for day_plan in itinerary:
                    print(f"\n第{day_plan['day']}天:")
                    for attraction in day_plan['attractions']:
                        print(f"- {attraction['name']} ({attraction['city']})")
        
        return result
    except Exception as e:
        print(f"请求失败: {e}")
        return None

if __name__ == "__main__":
    test_path_calculate()