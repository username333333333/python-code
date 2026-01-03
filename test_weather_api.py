import requests
import json

# 测试天气预测API
def test_weather_predict():
    url = "http://127.0.0.1:5000/api/weather/predict"
    
    # 测试数据
    data = {
        "city": "沈阳",
        "days": 3,
        "start_date": "2025-10-20"
    }
    
    # 发送请求
    print(f"发送请求到 {url}，数据: {data}")
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(data))
    
    # 打印响应
    print(f"响应状态码: {response.status_code}")
    response_data = response.json()
    print(f"响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
    
    if response_data.get("success"):
        predictions = response_data.get("predictions")
        print(f"预测结果数量: {len(predictions)}")
        for pred in predictions:
            print(f"日期: {pred.get('日期')}, 最高气温: {pred.get('最高气温')}, 最低气温: {pred.get('最低气温')}, 旅游评分: {pred.get('旅游评分')}, 推荐指数: {pred.get('推荐指数')}")
    else:
        print(f"请求失败: {response_data.get('message')}")

if __name__ == "__main__":
    test_weather_predict()