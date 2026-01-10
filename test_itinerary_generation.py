#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试行程生成功能，特别是当景点数量小于旅行天数时的情况
"""

from app import create_app
from app.services.path_optimization_service import PathOptimizationService
from app.services.map_service import MapService

app = create_app()

with app.app_context():
    print("开始测试行程生成功能...")
    
    # 初始化服务
    path_service = PathOptimizationService()
    map_service = MapService()
    
    # 测试用例1：景点数量小于旅行天数
    print("\n测试用例1：景点数量小于旅行天数")
    print("-" * 50)
    
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
        
        # 打印结果
        print(f"行程生成成功！")
        print(f"生成的行程天数: {len(result['itinerary'])}")
        
        # 检查每天是否有景点
        all_days_have_attractions = True
        for day_plan in result['itinerary']:
            day = day_plan['day']
            attraction_count = len(day_plan['attractions'])
            print(f"第{day}天景点数量: {attraction_count}")
            if attraction_count == 0:
                all_days_have_attractions = False
        
        if all_days_have_attractions:
            print("✅ 所有天数都有景点安排")
        else:
            print("❌ 存在没有景点安排的天数")
            
        # 测试地图生成
        try:
            map_obj = map_service.generate_travel_map(
                itinerary=result['itinerary'],
                start_city="沈阳",
                target_city="沈阳"
            )
            print("✅ 地图生成成功")
        except Exception as e:
            print(f"❌ 地图生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ 行程生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例2：景点数量等于旅行天数
    print("\n测试用例2：景点数量等于旅行天数")
    print("-" * 50)
    
    selected_attractions = [
        {"name": "沈阳故宫", "city": "沈阳"},
        {"name": "北陵公园", "city": "沈阳"},
        {"name": "棋盘山风景区", "city": "沈阳"},
        {"name": "沈阳方特欢乐世界", "city": "沈阳"},
        {"name": "沈阳森林动物园", "city": "沈阳"}
    ]
    
    try:
        # 生成行程
        result = path_service.generate_closed_loop_path(
            start_city="沈阳",
            days=5,
            preferences=preferences,
            target_city="沈阳",
            selected_attractions=selected_attractions
        )
        
        # 打印结果
        print(f"行程生成成功！")
        print(f"生成的行程天数: {len(result['itinerary'])}")
        
        # 检查每天是否有景点
        all_days_have_attractions = True
        for day_plan in result['itinerary']:
            day = day_plan['day']
            attraction_count = len(day_plan['attractions'])
            print(f"第{day}天景点数量: {attraction_count}")
            if attraction_count == 0:
                all_days_have_attractions = False
        
        if all_days_have_attractions:
            print("✅ 所有天数都有景点安排")
        else:
            print("❌ 存在没有景点安排的天数")
            
    except Exception as e:
        print(f"❌ 行程生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例3：景点数量大于旅行天数
    print("\n测试用例3：景点数量大于旅行天数")
    print("-" * 50)
    
    selected_attractions = [
        {"name": "沈阳故宫", "city": "沈阳"},
        {"name": "北陵公园", "city": "沈阳"},
        {"name": "棋盘山风景区", "city": "沈阳"},
        {"name": "沈阳方特欢乐世界", "city": "沈阳"},
        {"name": "沈阳森林动物园", "city": "沈阳"},
        {"name": "沈阳世博园", "city": "沈阳"},
        {"name": "怪坡风景区", "city": "沈阳"}
    ]
    
    try:
        # 生成行程
        result = path_service.generate_closed_loop_path(
            start_city="沈阳",
            days=5,
            preferences=preferences,
            target_city="沈阳",
            selected_attractions=selected_attractions
        )
        
        # 打印结果
        print(f"行程生成成功！")
        print(f"生成的行程天数: {len(result['itinerary'])}")
        
        # 检查每天是否有景点
        all_days_have_attractions = True
        for day_plan in result['itinerary']:
            day = day_plan['day']
            attraction_count = len(day_plan['attractions'])
            print(f"第{day}天景点数量: {attraction_count}")
            if attraction_count == 0:
                all_days_have_attractions = False
        
        if all_days_have_attractions:
            print("✅ 所有天数都有景点安排")
        else:
            print("❌ 存在没有景点安排的天数")
            
    except Exception as e:
        print(f"❌ 行程生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("测试完成！")
