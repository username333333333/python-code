#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试单向路径显示功能，包括不同路径复杂度、数据量和边界条件
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
    
    def test_one_way_path(start_city, target_city, days, test_name):
        """测试单向路径显示功能"""
        print(f"\n=== {test_name} ===")
        print(f"测试从{start_city}到{target_city}的单向路径显示，天数: {days}...")
        
        try:
            # 初始化服务
            path_service = PathOptimizationService()
            map_service = MapService()
            
            # 生成路径
            path_result = path_service.generate_closed_loop_path(
                start_city=start_city,
                days=days,
                preferences={"min_rating": 4.0},
                target_city=target_city
            )
            
            itinerary = path_result['itinerary']
            start_city_from_result = path_result.get('start_city', start_city)
            target_city_from_result = path_result.get('target_city', target_city)
            
            print(f"生成行程成功，共{len(itinerary)}天")
            
            # 打印行程详情
            for day_plan in itinerary:
                print(f"\n第{day_plan['day']}天行程：")
                for i, attraction_info in enumerate(day_plan['attractions']):
                    attraction = attraction_info['attraction'] if isinstance(attraction_info, dict) and 'attraction' in attraction_info else attraction_info
                    print(f"  {i+1}. {attraction.city} - {attraction.name} ({attraction.type})")
            
            # 生成地图
            print(f"\n生成从{start_city}到{target_city}的地图...")
            map_object = map_service.generate_travel_map(itinerary, start_city_from_result, target_city_from_result)
            
            # 保存地图
            map_html_path = f"one_way_path_{test_name}.html"
            map_object.save(map_html_path)
            print(f"地图已保存到 {map_html_path}")
            
            print(f"✅ {test_name} 通过")
            return True
        
        except Exception as e:
            print(f"❌ {test_name} 失败：{str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def main():
        """运行所有测试"""
        print("开始测试单向路径显示功能...")
        
        test_results = []
        
        # 测试1：简单单向路径（2天）
        test_results.append(test_one_way_path("大连", "鞍山", 2, "简单单向路径"))
        
        # 测试2：复杂单向路径（3天）
        test_results.append(test_one_way_path("沈阳", "丹东", 3, "复杂单向路径"))
        
        # 测试3：长距离单向路径
        test_results.append(test_one_way_path("锦州", "铁岭", 2, "长距离单向路径"))
        
        # 测试4：单天单向路径
        test_results.append(test_one_way_path("本溪", "辽阳", 1, "单天单向路径"))
        
        # 测试5：边界条件 - 相同城市（应该生成闭环路径）
        test_results.append(test_one_way_path("大连", "大连", 2, "边界条件-相同城市"))
        
        # 汇总测试结果
        print(f"\n=== 测试结果汇总 ===")
        print(f"总测试数: {len(test_results)}")
        print(f"通过测试数: {sum(test_results)}")
        print(f"失败测试数: {len(test_results) - sum(test_results)}")
        
        if all(test_results):
            print(f"✅ 所有测试通过！单向路径显示功能正常。")
            return 0
        else:
            print(f"❌ 部分测试失败！需要进一步检查。")
            return 1
    
    # 运行测试
    sys.exit(main())
