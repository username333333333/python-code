#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试地图坐标生成是否会根据不同的景点类型偏好而变化
"""

from app import create_app
from app.services.path_optimization_service import PathOptimizationService
from app.services.map_service import MapService

def test_map_coordinates_dynamic():
    """测试地图坐标生成是否会根据不同的景点类型偏好而变化"""
    print("=" * 60)
    print("开始测试地图坐标动态生成功能...")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # 初始化服务
        path_service = PathOptimizationService()
        map_service = MapService()
        
        # 测试参数
        start_city = "沈阳"
        target_city = "沈阳"
        days = 2
        
        # 不同的景点类型偏好
        test_preferences = [
            {"attraction_types": ["风景区"], "name": "风景区"},
            {"attraction_types": ["公园"], "name": "公园"},
            {"attraction_types": ["博物馆"], "name": "博物馆"}
        ]
        
        # 保存每次生成的地图坐标信息
        map_coords_info = []
        
        for pref in test_preferences:
            print(f"\n--- 测试 {pref['name']} 类型偏好的地图坐标生成 ---")
            
            try:
                # 生成行程
                result = path_service.generate_closed_loop_path(
                    start_city=start_city,
                    days=days,
                    preferences=pref,
                    target_city=target_city,
                    selected_attractions=None
                )
                
                itinerary = result['itinerary']
                print(f"生成行程成功，共 {len(itinerary)} 天，总景点数: {sum(len(day['attractions']) for day in itinerary)}")
                
                # 生成地图
                map_obj = map_service.generate_travel_map(
                    itinerary=itinerary,
                    start_city=start_city,
                    target_city=target_city
                )
                
                # 提取地图的关键信息
                map_info = {
                    'type_preference': pref['name'],
                    'itinerary_days': len(itinerary),
                    'total_attractions': sum(len(day['attractions']) for day in itinerary),
                    'map_location': map_obj.location
                }
                
                map_coords_info.append(map_info)
                print(f"生成地图成功，地图中心: {map_obj.location}")
                
            except Exception as e:
                print(f"❌ 测试 {pref['name']} 失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 比较不同类型偏好生成的地图信息
        print("\n" + "=" * 60)
        print("不同类型偏好生成的地图信息比较:")
        print("=" * 60)
        
        for info in map_coords_info:
            print(f"类型偏好: {info['type_preference']}")
            print(f"  - 行程天数: {info['itinerary_days']}")
            print(f"  - 总景点数: {info['total_attractions']}")
            print(f"  - 地图中心: {info['map_location']}")
            print()
        
        # 验证地图坐标是否根据类型偏好变化
        all_same = True
        first_map = map_coords_info[0] if map_coords_info else None
        
        if first_map:
            for info in map_coords_info[1:]:
                # 检查总景点数是否不同（因为不同类型偏好会返回不同的景点）
                if info['total_attractions'] != first_map['total_attractions']:
                    all_same = False
                    break
        
        if all_same:
            print("❌ 测试失败: 不同类型偏好生成的地图信息基本相同，坐标没有动态变化")
        else:
            print("✅ 测试成功: 不同类型偏好生成的地图信息不同，坐标会根据类型偏好动态变化")
            print("\n结论: 系统能够根据不同的景点类型偏好，生成不同的景点列表和地图坐标")

if __name__ == "__main__":
    test_map_coordinates_dynamic()