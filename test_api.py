import requests
import json

# 测试路径生成接口
url = 'http://127.0.0.1:5000/path/calculate'
headers = {'Content-Type': 'application/json'}
data = {
    'start_city': '沈阳',
    'target_city': '大连',
    'days': 3,
    'preferences': {
        'attraction_types': ['博物馆', '公园'],
        'min_rating': 4.0
    }
}

print(f'发送请求到 {url}')
print(f'请求数据: {json.dumps(data, ensure_ascii=False)}')

try:
    response = requests.post(url, headers=headers, json=data, timeout=30)
    print(f'响应状态码: {response.status_code}')
    print(f'响应头: {dict(response.headers)}')
    print(f'响应内容: {response.text}')
    
    # 尝试解析JSON
    if response.headers.get('Content-Type') == 'application/json':
        try:
            result = response.json()
            print(f'\n解析后的JSON响应:')
            print(f'成功: {result.get("success")}')
            if result.get('itinerary'):
                print(f'行程天数: {len(result["itinerary"])}')
                for day, day_plan in enumerate(result["itinerary"]):
                    print(f'第 {day+1} 天:')
                    print(f'  景点数量: {len(day_plan.get("attractions", []))}')
                    for attr in day_plan.get("attractions", []):
                        print(f'    - {attr.get("name")} ({attr.get("city")})')
        except json.JSONDecodeError as e:
            print(f'JSON解析失败: {e}')
            
except requests.exceptions.RequestException as e:
    print(f'请求失败: {e}')
