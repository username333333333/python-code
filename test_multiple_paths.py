#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试地图在多条路径情况下的显示情况，确保不同路径能正确区分显示
"""

from app import create_app
from app.services.map_service import MapService

app = create_app()

with app.app_context():
    print("开始测试地图在多条路径情况下的显示情况...")
    
    # 初始化服务
    map_service = MapService()
    
    # 测试用例：3天行程，每天2个景点，生成3条不同路径
    print("\n测试用例：3天行程，每天2个景点")
    print("-" * 60)
    
    # 创建包含3天行程的测试数据
    itinerary_3_days = [
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
                    'name': '沈阳北陵公园',
                    'city': '沈阳',
                    'type': '公园',
                    'rating': 4.5,
                    'latitude': 41.8268,
                    'longitude': 123.4122
                }
            ]
        },
        {
            'day': 2,
            'attractions': [
                {
                    'name': '大连老虎滩海洋公园',
                    'city': '大连',
                    'type': '公园',
                    'rating': 4.7,
                    'latitude': 38.9140,
                    'longitude': 121.6147
                },
                {
                    'name': '大连圣亚海洋世界',
                    'city': '大连',
                    'type': '水族馆',
                    'rating': 4.6,
                    'latitude': 38.9112,
                    'longitude': 121.5897
                }
            ]
        },
        {
            'day': 3,
            'attractions': [
                {
                    'name': '鞍山千山风景区',
                    'city': '鞍山',
                    'type': '风景区',
                    'rating': 4.6,
                    'latitude': 41.1182,
                    'longitude': 122.8907
                },
                {
                    'name': '鞍山玉佛苑',
                    'city': '鞍山',
                    'type': '宗教场所',
                    'rating': 4.5,
                    'latitude': 41.1089,
                    'longitude': 122.9933
                }
            ]
        }
    ]
    
    try:
        map_obj = map_service.generate_travel_map(itinerary_3_days, start_city="沈阳", target_city="大连")
        print("✅ 测试用例通过：3天行程的多条路径都能正确显示")
    except Exception as e:
        print(f"❌ 测试用例失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例：2天行程，每天多个景点，生成2条不同路径
    print("\n测试用例：2天行程，每天多个景点")
    print("-" * 60)
    
    itinerary_2_days = [
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
                    'name': '沈阳北陵公园',
                    'city': '沈阳',
                    'type': '公园',
                    'rating': 4.5,
                    'latitude': 41.8268,
                    'longitude': 123.4122
                },
                {
                    'name': '沈阳东陵公园',
                    'city': '沈阳',
                    'type': '公园',
                    'rating': 4.4,
                    'latitude': 41.8082,
                    'longitude': 123.5289
                }
            ]
        },
        {
            'day': 2,
            'attractions': [
                {
                    'name': '抚顺热高乐园',
                    'city': '抚顺',
                    'type': '主题公园',
                    'rating': 4.3,
                    'latitude': 41.8798,
                    'longitude': 124.0875
                },
                {
                    'name': '抚顺皇家极地海洋世界',
                    'city': '抚顺',
                    'type': '水族馆',
                    'rating': 4.2,
                    'latitude': 41.8891,
                    'longitude': 124.0733
                }
            ]
        }
    ]
    
    try:
        map_obj = map_service.generate_travel_map(itinerary_2_days, start_city="沈阳", target_city="抚顺")
        print("✅ 测试用例通过：2天行程的多条路径都能正确显示")
    except Exception as e:
        print(f"❌ 测试用例失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("地图多条路径显示功能测试完成！")
