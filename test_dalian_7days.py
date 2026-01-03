import requests
import json

# 测试路径计算API，目标城市为大连，旅行天数为7天
def test_path_calculate():
    print("测试路径计算API，目标城市：大连，旅行天数：7天...")
    url = "http://127.0.0.1:5000/path/calculate"
    data = {
        "start_city": "沈阳",
        "target_city": "大连",
        "days": 7,
        "preferences": {
            "attraction_types": ["自然景观", "人文景观", "主题公园"],
            "min_rating": 4.0
        }
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers, timeout=30)
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        if result and result.get("success"):
            print("路径生成成功！")
            itinerary = result.get("itinerary")
            if itinerary:
                print(f"\n生成了 {len(itinerary)} 天的行程：")
                for day_plan in itinerary:
                    print(f"\n第{day_plan['day']}天: {len(day_plan['attractions'])}个景点")
                    for attraction in day_plan['attractions'][:3]:  # 只显示前3个景点
                        print(f"- {attraction['name']} ({attraction['city']})")
                    if len(day_plan['attractions']) > 3:
                        print(f"... 还有 {len(day_plan['attractions']) - 3} 个景点")
        else:
            print(f"路径生成失败：{result.get('message')}")
        
        return result
    except Exception as e:
        print(f"请求失败: {e}")
        return None

if __name__ == "__main__":
    test_path_calculate()