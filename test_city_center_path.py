#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试城市中心点作为起点的路径生成功能
"""

import sys
import os
from flask import Flask

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入应用
from app import create_app

# 创建Flask应用实例，以便在应用上下文中运行测试
app = create_app()


with app.app_context():
    from app.services.path_optimization_service import PathOptimizationService
    from app.services.map_service import MapService
    
    def test_city_center_path():
        """测试城市中心点作为起点的路径生成"""
        print("开始测试城市中心点作为起点的路径生成功能...")
        
        # 初始化服务
        path_service = PathOptimizationService()
        map_service = MapService()
        
        # 测试数据：起点城市和目标城市不同
        start_city = "大连"
        target_city = "鞍山"
        days = 2
        
        # 测试路径生成
        print(f"测试从{start_city}到{target_city}的路径生成，使用{start_city}中心点作为起点...")
        
        try:
            # 生成路径
            path_result = path_service.generate_closed_loop_path(
                start_city=start_city,
                days=days,
                preferences={"min_rating": 4.0},
                target_city=target_city
            )
            
            itinerary = path_result['itinerary']
            print(f"生成行程成功，共{len(itinerary)}天")
            
            # 打印行程详情
            for day_plan in itinerary:
                print(f"\n第{day_plan['day']}天行程：")
                for i, attraction_info in enumerate(day_plan['attractions']):
                    attraction = attraction_info['attraction'] if isinstance(attraction_info, dict) and 'attraction' in attraction_info else attraction_info
                    print(f"  {i+1}. {attraction.city} - {attraction.name} ({attraction.type})")
            
            # 生成地图
            print(f"\n生成从{start_city}到{target_city}的地图...")
            map_object = map_service.generate_travel_map(itinerary, start_city, target_city)
            
            # 保存地图
            map_html_path = f"city_center_path_{start_city}_{target_city}.html"
            map_object.save(map_html_path)
            print(f"地图已保存到 {map_html_path}")
            
            print("\n城市中心点作为起点的路径生成测试成功！")
            return True
        
        except Exception as e:
            print(f"测试失败：{str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    # 运行测试
    test_city_center_path()
