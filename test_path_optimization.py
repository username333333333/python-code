#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试路径优化服务
"""

import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 创建Flask应用上下文
from app import create_app
app = create_app()

from app.services.path_optimization_service import PathOptimizationService
from app.services.map_service import MapService


def test_path_optimization():
    """测试路径优化服务"""
    print("测试路径优化服务...")
    
    try:
        # 测试参数
        start_city = "沈阳"
        days = 3
        preferences = {
            'attraction_types': ['博物馆', '公园', '风景区'],
            'min_rating': 4.0
        }
        
        print(f"生成从{start_city}出发，{days}天的闭环路径...")
        
        with app.app_context():
            # 初始化服务
            path_service = PathOptimizationService()
            
            # 生成路径
            itinerary = path_service.generate_closed_loop_path(
                start_city, days, preferences
            )
            
            print(f"成功生成{len(itinerary)}天的行程")
            
            # 打印行程
            for day_plan in itinerary:
                print(f"\n第{day_plan['day']}天:")
                for i, attraction in enumerate(day_plan['attractions']):
                    print(f"  {i+1}. {attraction.name} ({attraction.city}) - {attraction.type}，评分: {attraction.rating}")
            
            return itinerary
        
    except Exception as e:
        print(f"路径优化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_map_generation(itinerary):
    """测试地图生成服务"""
    if not itinerary:
        print("没有行程数据，跳过地图生成测试")
        return
    
    print("\n测试地图生成服务...")
    
    try:
        with app.app_context():
            # 初始化服务
            map_service = MapService()
            
            # 生成地图
            map_object = map_service.generate_closed_loop_map(itinerary)
            
            # 保存地图
            map_file = "test_closed_loop_map.html"
            map_object.save(map_file)
            
            print(f"成功生成地图，保存到: {map_file}")
            
    except Exception as e:
        print(f"地图生成测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_weather_adjustment(itinerary):
    """测试天气调整功能"""
    if not itinerary:
        print("没有行程数据，跳过分天气调整测试")
        return
    
    print("\n测试天气调整功能...")
    
    try:
        with app.app_context():
            # 初始化服务
            path_service = PathOptimizationService()
            
            # 模拟天气预测数据
            weather_forecast = [
                {
                    'date': '2025-12-27',
                    'weather': '小雨',
                    'temperature': 5,
                    'wind': '3级'
                },
                {
                    'date': '2025-12-28',
                    'weather': '晴',
                    'temperature': 10,
                    'wind': '2级'
                },
                {
                    'date': '2025-12-29',
                    'weather': '多云',
                    'temperature': 8,
                    'wind': '4级'
                }
            ]
            
            # 调整路径
            adjusted_itinerary = path_service.optimize_path_for_weather(
                itinerary, weather_forecast
            )
            
            print(f"成功调整行程，调整后行程长度: {len(adjusted_itinerary)}")
            
            # 打印调整后的行程
            for day_plan in adjusted_itinerary:
                print(f"\n第{day_plan['day']}天 (调整: {day_plan['adjusted']}):")
                print(f"  天气: {day_plan['weather']['weather']}，温度: {day_plan['weather']['temperature']}°C")
                for i, attraction in enumerate(day_plan['attractions']):
                    print(f"  {i+1}. {attraction.name} ({attraction.city}) - {attraction.type}")
            
            return adjusted_itinerary
            
    except Exception as e:
        print(f"天气调整测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_different_city_combinations():
    """测试不同的起点和目标城市组合"""
    print("\n=== 测试不同的起点和目标城市组合 ===")
    
    city_combinations = [
        ("沈阳", "大连"),
        ("大连", "沈阳"),
        ("沈阳", "丹东"),
        ("丹东", "沈阳"),
        ("沈阳", "鞍山"),
        ("沈阳", "沈阳")  # 起点和终点相同的情况
    ]
    
    with app.app_context():
        path_service = PathOptimizationService()
        
        for start_city, target_city in city_combinations:
            print(f"\n测试从{start_city}到{target_city}的路径生成...")
            try:
                itinerary = path_service.generate_closed_loop_path(
                    start_city, 2, {"attraction_types": ["博物馆", "公园"], "min_rating": 3.5},
                    target_city=target_city
                )
                print(f"  成功生成{len(itinerary)}天的行程")
            except Exception as e:
                print(f"  测试失败: {e}")


def test_different_days():
    """测试不同的旅行天数"""
    print("\n=== 测试不同的旅行天数 ===")
    
    days_list = [1, 2, 3, 5, 7]  # 包括边界情况1天和7天
    
    with app.app_context():
        path_service = PathOptimizationService()
        
        for days in days_list:
            print(f"\n测试生成{days}天的路径...")
            try:
                itinerary = path_service.generate_closed_loop_path(
                    "沈阳", days, {"attraction_types": ["博物馆", "公园"], "min_rating": 3.5}
                )
                print(f"  成功生成{len(itinerary)}天的行程")
                assert len(itinerary) == days, f"行程天数不匹配，预期{days}天，实际{len(itinerary)}天"
            except Exception as e:
                print(f"  测试失败: {e}")


def test_different_preferences():
    """测试不同的景点类型偏好"""
    print("\n=== 测试不同的景点类型偏好 ===")
    
    preferences_list = [
        {"attraction_types": ["博物馆"], "min_rating": 4.0},
        {"attraction_types": ["公园"], "min_rating": 3.0},
        {"attraction_types": ["风景区"], "min_rating": 4.5},
        {"attraction_types": ["历史古迹"], "min_rating": 3.5},
        {"attraction_types": [], "min_rating": 0.0}  # 空的景点类型偏好
    ]
    
    with app.app_context():
        path_service = PathOptimizationService()
        
        for preferences in preferences_list:
            types = preferences["attraction_types"]
            rating = preferences["min_rating"]
            print(f"\n测试景点类型偏好: {types}, 最低评分: {rating}...")
            try:
                itinerary = path_service.generate_closed_loop_path(
                    "沈阳", 2, preferences
                )
                print(f"  成功生成{len(itinerary)}天的行程")
            except Exception as e:
                print(f"  测试失败: {e}")


def test_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    with app.app_context():
        path_service = PathOptimizationService()
        
        # 测试空的景点列表情况（模拟没有符合条件的景点）
        print("\n测试空的景点列表情况...")
        try:
            # 使用不存在的景点类型，模拟没有符合条件的景点
            itinerary = path_service.generate_closed_loop_path(
                "沈阳", 2, {"attraction_types": ["不存在的类型"], "min_rating": 5.0}
            )
            print(f"  成功生成{len(itinerary)}天的行程")
        except Exception as e:
            print(f"  测试失败: {e}")
        
        # 测试天气数据为空的情况
        print("\n测试天气数据为空的情况...")
        try:
            itinerary = path_service.generate_closed_loop_path(
                "沈阳", 2, {"attraction_types": ["博物馆"], "min_rating": 4.0}
            )
            # 模拟空的天气数据
            adjusted_itinerary = path_service.optimize_path_for_weather(itinerary, [])
            print(f"  成功处理空天气数据，调整后行程长度: {len(adjusted_itinerary)}")
        except Exception as e:
            print(f"  测试失败: {e}")


if __name__ == "__main__":
    print("=== 辽宁省智慧旅游路径优化系统测试 ===")
    
    # 测试路径优化
    itinerary = test_path_optimization()
    
    # 测试天气调整
    adjusted_itinerary = test_weather_adjustment(itinerary)
    
    # 测试地图生成（使用调整后的行程）
    test_map_generation(adjusted_itinerary or itinerary)
    
    # 测试不同的起点和目标城市组合
    test_different_city_combinations()
    
    # 测试不同的旅行天数
    test_different_days()
    
    # 测试不同的景点类型偏好
    test_different_preferences()
    
    # 测试边界情况
    test_edge_cases()
    
    print("\n=== 测试完成 ===")
