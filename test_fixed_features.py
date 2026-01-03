#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的功能：
1. 行程规划模块是否不再错误显示起点地址
2. 单向路径地图是否能正常显示
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
    
    def test_fixed_features():
        """测试修复后的功能"""
        print("开始测试修复后的功能...")
        
        # 初始化服务
        path_service = PathOptimizationService()
        map_service = MapService()
        
        # 测试数据：起点城市和目标城市不同
        start_city = "大连"
        target_city = "鞍山"
        days = 2
        
        # 测试1：行程规划模块是否不再错误显示起点地址
        print(f"\n=== 测试1：行程规划模块 ===")
        print(f"测试从{start_city}到{target_city}的行程规划，确保不错误显示起点地址...")
        
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
            
            # 打印行程详情，检查是否错误显示起点地址
            has_incorrect_start = False
            for day_plan in itinerary:
                print(f"\n第{day_plan['day']}天行程：")
                for i, attraction_info in enumerate(day_plan['attractions']):
                    attraction = attraction_info['attraction'] if isinstance(attraction_info, dict) and 'attraction' in attraction_info else attraction_info
                    print(f"  {i+1}. {attraction.city} - {attraction.name} ({attraction.type})")
                    
                    # 检查是否错误显示起点地址
                    if attraction.type == "城市中心" and attraction.city == start_city:
                        has_incorrect_start = True
                        print(f"  ❌ 错误：行程中包含了未选择的起点地址 - {attraction.name}")
            
            if not has_incorrect_start:
                print(f"\n✅ 测试1通过：行程规划模块未错误显示起点地址")
            else:
                print(f"\n❌ 测试1失败：行程规划模块仍然错误显示起点地址")
        
        except Exception as e:
            print(f"\n❌ 测试1失败：行程规划生成出错 - {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 测试2：单向路径地图是否能正常显示
        print(f"\n=== 测试2：单向路径地图 ===")
        print(f"测试从{start_city}到{target_city}的地图生成，确保单向路径能正常显示...")
        
        try:
            # 重新生成路径，确保有新的itinerary
            path_result = path_service.generate_closed_loop_path(
                start_city=start_city,
                days=days,
                preferences={"min_rating": 4.0},
                target_city=target_city
            )
            
            itinerary = path_result['itinerary']
            
            # 生成地图
            print(f"生成从{start_city}到{target_city}的地图...")
            map_object = map_service.generate_travel_map(itinerary, start_city, target_city)
            
            # 保存地图
            map_html_path = f"fixed_path_map_{start_city}_{target_city}.html"
            map_object.save(map_html_path)
            print(f"地图已保存到 {map_html_path}")
            
            print(f"\n✅ 测试2通过：单向路径地图能正常生成")
        
        except Exception as e:
            print(f"\n❌ 测试2失败：地图生成出错 - {str(e)}")
            import traceback
            traceback.print_exc()
        
        print(f"\n=== 测试完成 ===")
    
    # 运行测试
    test_fixed_features()
