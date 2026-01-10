#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试地图生成功能，确保在各种情况下都能正常工作
"""

from app import create_app
from app.services.path_optimization_service import PathOptimizationService
from app.services.map_service import MapService

app = create_app()

with app.app_context():
    print("开始全面测试地图生成功能...")
    
    # 初始化服务
    path_service = PathOptimizationService()
    map_service = MapService()
    
    # 测试用例1：所有景点坐标相同（城市中心坐标）
    print("\n测试用例1：所有景点坐标相同（城市中心坐标）")
    print("-" * 60)
    
    # 模拟用户选择了2个景点，但旅行天数为5天
    selected_attractions = [
        {"name": "沈阳故宫", "city": "沈阳"},
        {"name": "北陵公园", "city": "沈阳"}
    ]
    
    preferences = {
        "min_rating": 4.0,
        "attraction_types": ["风景区"]
    }
    
    try:
        # 生成行程
        result = path_service.generate_closed_loop_path(
            start_city="沈阳",
            days=5,
            preferences=preferences,
            target_city="沈阳",
            selected_attractions=selected_attractions
        )
        
        # 生成地图
        map_obj = map_service.generate_travel_map(
            itinerary=result['itinerary'],
            start_city="沈阳",
            target_city="沈阳"
        )
        
        print("✅ 测试用例1通过：所有景点坐标相同时，地图生成成功")
    except Exception as e:
        print(f"❌ 测试用例1失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例2：跨城市旅行（起点城市和目标城市不同）
    print("\n测试用例2：跨城市旅行（起点城市和目标城市不同）")
    print("-" * 60)
    
    try:
        # 生成跨城市行程
        cross_city_result = path_service.generate_closed_loop_path(
            start_city="沈阳",
            days=3,
            preferences=preferences,
            target_city="大连",
            selected_attractions=[]
        )
        
        # 生成地图
        cross_city_map = map_service.generate_travel_map(
            itinerary=cross_city_result['itinerary'],
            start_city="沈阳",
            target_city="大连"
        )
        
        print("✅ 测试用例2通过：跨城市旅行时，地图生成成功")
    except Exception as e:
        print(f"❌ 测试用例2失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例3：单个景点行程
    print("\n测试用例3：单个景点行程")
    print("-" * 60)
    
    single_attraction = [
        {"name": "沈阳故宫", "city": "沈阳"}
    ]
    
    try:
        # 生成单景点行程
        single_result = path_service.generate_closed_loop_path(
            start_city="沈阳",
            days=1,
            preferences=preferences,
            target_city="沈阳",
            selected_attractions=single_attraction
        )
        
        # 生成地图
        single_map = map_service.generate_travel_map(
            itinerary=single_result['itinerary'],
            start_city="沈阳",
            target_city="沈阳"
        )
        
        print("✅ 测试用例3通过：单个景点行程时，地图生成成功")
    except Exception as e:
        print(f"❌ 测试用例3失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例4：多个景点，坐标分布广泛
    print("\n测试用例4：多个景点，坐标分布广泛")
    print("-" * 60)
    
    multi_attractions = [
        {"name": "沈阳故宫", "city": "沈阳"},
        {"name": "大连老虎滩海洋公园", "city": "大连"},
        {"name": "鞍山千山风景区", "city": "鞍山"},
        {"name": "丹东鸭绿江", "city": "丹东"},
        {"name": "锦州笔架山", "city": "锦州"}
    ]
    
    try:
        # 生成多景点行程
        multi_result = path_service.generate_closed_loop_path(
            start_city="沈阳",
            days=5,
            preferences=preferences,
            target_city="沈阳",
            selected_attractions=multi_attractions
        )
        
        # 生成地图
        multi_map = map_service.generate_travel_map(
            itinerary=multi_result['itinerary'],
            start_city="沈阳",
            target_city="沈阳"
        )
        
        print("✅ 测试用例4通过：多个景点，坐标分布广泛时，地图生成成功")
    except Exception as e:
        print(f"❌ 测试用例4失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例5：长时间行程（10天）
    print("\n测试用例5：长时间行程（10天）")
    print("-" * 60)
    
    try:
        # 生成长时间行程
        long_result = path_service.generate_closed_loop_path(
            start_city="沈阳",
            days=10,
            preferences=preferences,
            target_city="沈阳",
            selected_attractions=selected_attractions
        )
        
        # 生成地图
        long_map = map_service.generate_travel_map(
            itinerary=long_result['itinerary'],
            start_city="沈阳",
            target_city="沈阳"
        )
        
        print("✅ 测试用例5通过：长时间行程时，地图生成成功")
    except Exception as e:
        print(f"❌ 测试用例5失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("地图生成功能全面测试完成！")
