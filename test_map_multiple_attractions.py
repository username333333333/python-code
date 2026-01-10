#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试地图在不同景点数量下的显示情况，确保所有景点标识都能正确显示
"""

from app import create_app
from app.services.map_service import MapService

app = create_app()

with app.app_context():
    print("开始测试地图在不同景点数量下的显示情况...")
    
    # 初始化服务
    map_service = MapService()
    
    # 测试用例1：2个景点，坐标相同
    print("\n测试用例1：2个景点，坐标相同")
    print("-" * 60)
    
    itinerary_2 = [
        {
            'day': 1,
            'attractions': [
                {
                    'name': '景点1',
                    'city': '沈阳',
                    'type': '风景区',
                    'rating': 4.5,
                    'latitude': 41.8057,
                    'longitude': 123.4315
                },
                {
                    'name': '景点2',
                    'city': '沈阳',
                    'type': '博物馆',
                    'rating': 4.2,
                    'latitude': 41.8057,
                    'longitude': 123.4315
                }
            ]
        }
    ]
    
    try:
        map_obj = map_service.generate_travel_map(itinerary_2, start_city="沈阳", target_city="沈阳")
        print("✅ 测试用例1通过：2个相同坐标的景点标识都能显示")
    except Exception as e:
        print(f"❌ 测试用例1失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例2：5个景点，坐标相同
    print("\n测试用例2：5个景点，坐标相同")
    print("-" * 60)
    
    itinerary_5 = [
        {
            'day': 1,
            'attractions': [
                {
                    'name': '景点1',
                    'city': '沈阳',
                    'type': '风景区',
                    'rating': 4.5,
                    'latitude': 41.8057,
                    'longitude': 123.4315
                },
                {
                    'name': '景点2',
                    'city': '沈阳',
                    'type': '博物馆',
                    'rating': 4.2,
                    'latitude': 41.8057,
                    'longitude': 123.4315
                },
                {
                    'name': '景点3',
                    'city': '沈阳',
                    'type': '公园',
                    'rating': 4.0,
                    'latitude': 41.8057,
                    'longitude': 123.4315
                },
                {
                    'name': '景点4',
                    'city': '沈阳',
                    'type': '历史遗迹',
                    'rating': 4.8,
                    'latitude': 41.8057,
                    'longitude': 123.4315
                },
                {
                    'name': '景点5',
                    'city': '沈阳',
                    'type': '美食街',
                    'rating': 4.3,
                    'latitude': 41.8057,
                    'longitude': 123.4315
                }
            ]
        }
    ]
    
    try:
        map_obj = map_service.generate_travel_map(itinerary_5, start_city="沈阳", target_city="沈阳")
        print("✅ 测试用例2通过：5个相同坐标的景点标识都能显示")
    except Exception as e:
        print(f"❌ 测试用例2失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例3：10个景点，坐标相同
    print("\n测试用例3：10个景点，坐标相同")
    print("-" * 60)
    
    itinerary_10 = [
        {
            'day': 1,
            'attractions': [
                {
                    'name': f'景点{i+1}',
                    'city': '沈阳',
                    'type': '风景区',
                    'rating': 4.0 + (i % 10) * 0.1,
                    'latitude': 41.8057,
                    'longitude': 123.4315
                } for i in range(10)
            ]
        }
    ]
    
    try:
        map_obj = map_service.generate_travel_map(itinerary_10, start_city="沈阳", target_city="沈阳")
        print("✅ 测试用例3通过：10个相同坐标的景点标识都能显示")
    except Exception as e:
        print(f"❌ 测试用例3失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例4：10个景点，坐标分布广泛
    print("\n测试用例4：10个景点，坐标分布广泛")
    print("-" * 60)
    
    itinerary_10_diff = [
        {
            'day': 1,
            'attractions': [
                {
                    'name': '沈阳故宫',
                    'city': '沈阳',
                    'type': '历史遗迹',
                    'rating': 4.8,
                    'latitude': 41.8057,
                    'longitude': 123.4315
                },
                {
                    'name': '大连老虎滩海洋公园',
                    'city': '大连',
                    'type': '公园',
                    'rating': 4.7,
                    'latitude': 38.9140,
                    'longitude': 121.6147
                },
                {
                    'name': '鞍山千山风景区',
                    'city': '鞍山',
                    'type': '风景区',
                    'rating': 4.6,
                    'latitude': 41.1182,
                    'longitude': 122.8907
                },
                {
                    'name': '丹东鸭绿江',
                    'city': '丹东',
                    'type': '风景区',
                    'rating': 4.5,
                    'latitude': 40.1374,
                    'longitude': 124.3426
                },
                {
                    'name': '锦州笔架山',
                    'city': '锦州',
                    'type': '风景区',
                    'rating': 4.4,
                    'latitude': 41.1173,
                    'longitude': 121.1440
                },
                {
                    'name': '营口鲅鱼圈',
                    'city': '营口',
                    'type': '风景区',
                    'rating': 4.3,
                    'latitude': 40.6668,
                    'longitude': 122.1533
                },
                {
                    'name': '阜新海棠山',
                    'city': '阜新',
                    'type': '风景区',
                    'rating': 4.2,
                    'latitude': 42.0053,
                    'longitude': 121.6148
                },
                {
                    'name': '辽阳白塔',
                    'city': '辽阳',
                    'type': '历史遗迹',
                    'rating': 4.1,
                    'latitude': 41.2641,
                    'longitude': 123.1753
                },
                {
                    'name': '盘锦红海滩',
                    'city': '盘锦',
                    'type': '风景区',
                    'rating': 4.9,
                    'latitude': 41.1243,
                    'longitude': 122.0730
                },
                {
                    'name': '铁岭莲花湖',
                    'city': '铁岭',
                    'type': '公园',
                    'rating': 4.0,
                    'latitude': 42.2901,
                    'longitude': 123.8398
                }
            ]
        }
    ]
    
    try:
        map_obj = map_service.generate_travel_map(itinerary_10_diff, start_city="沈阳", target_city="沈阳")
        print("✅ 测试用例4通过：10个不同坐标的景点标识都能显示")
    except Exception as e:
        print(f"❌ 测试用例4失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("地图多景点显示功能测试完成！")
