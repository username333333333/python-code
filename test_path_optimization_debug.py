#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径优化功能调试脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.services.path_optimization_service import PathOptimizationService
from app.services.recommendation_service import RecommendationService


def test_recommendation_service():
    """测试推荐服务是否能正常加载数据"""
    print("=== 测试推荐服务 ===")
    try:
        # 初始化推荐服务
        recommendation_service = RecommendationService(data_dir="data")
        print(f"推荐服务初始化成功，景点数据行数: {len(recommendation_service.attractions_df)}")
        print(f"所有城市: {recommendation_service.get_all_cities()}")
        print(f"所有景点类型: {recommendation_service.get_attraction_types()}")
        
        # 测试根据类型推荐
        test_city = "大连"
        test_type = "风景区"
        recommendations = recommendation_service.recommend_by_attraction_type(
            attraction_type=test_type,
            city=test_city,
            top_n=5
        )
        print(f"\n根据{test_type}类型推荐的{test_city}景点:")
        if not recommendations.empty:
            print(recommendations[['景点名称', '景点类型', '评分']])
        else:
            print(f"没有找到{test_type}类型的{test_city}景点")
        
        return True
    except Exception as e:
        print(f"推荐服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_path_optimization_service():
    """测试路径优化服务"""
    print("\n=== 测试路径优化服务 ===")
    try:
        # 初始化路径优化服务
        path_service = PathOptimizationService()
        print("路径优化服务初始化成功")
        
        # 测试参数
        start_city = "大连"
        days = 3
        preferences = {
            'min_rating': 4.0,
            'attraction_types': ['风景区']
        }
        target_city = "大连"
        
        print(f"\n测试生成路径: 起点城市={start_city}, 目标城市={target_city}, 天数={days}, 偏好={preferences}")
        
        # 生成路径
        path_result = path_service.generate_closed_loop_path(
            start_city=start_city,
            days=days,
            preferences=preferences,
            target_city=target_city,
            selected_attractions=None
        )
        
        print(f"路径生成结果: {path_result.keys()}")
        itinerary = path_result.get('itinerary', [])
        print(f"行程天数: {len(itinerary)}")
        
        for i, day_plan in enumerate(itinerary):
            print(f"\n第{i+1}天景点数量: {len(day_plan['attractions'])}")
            for attr_info in day_plan['attractions']:
                attr = attr_info['attraction'] if isinstance(attr_info, dict) and 'attraction' in attr_info else attr_info
                print(f"  - {attr.name} ({attr.city}, {attr.type}, {attr.rating})")
        
        return len(itinerary) > 0 and any(len(day['attractions']) > 0 for day in itinerary)
        
    except Exception as e:
        print(f"路径优化服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_filter_attractions():
    """测试景点过滤功能"""
    print("\n=== 测试景点过滤功能 ===")
    try:
        # 初始化路径优化服务
        path_service = PathOptimizationService()
        
        # 测试参数
        preferences = {
            'min_rating': 4.0,
            'attraction_types': ['风景区']
        }
        start_city = "大连"
        target_city = "大连"
        
        print(f"测试过滤景点: 起点城市={start_city}, 目标城市={target_city}, 偏好={preferences}")
        
        # 调用过滤方法
        attractions = path_service._filter_attractions(preferences, start_city, target_city)
        
        print(f"过滤后景点数量: {len(attractions)}")
        for attr in attractions[:10]:  # 只显示前10个
            print(f"  - {attr.name} ({attr.city}, {attr.type}, {attr.rating})")
        
        return len(attractions) > 0
        
    except Exception as e:
        print(f"景点过滤测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("开始调试路径优化功能...")
    
    # 测试推荐服务
    rec_success = test_recommendation_service()
    
    # 测试景点过滤
    filter_success = test_filter_attractions()
    
    # 测试路径生成
    path_success = test_path_optimization_service()
    
    print(f"\n=== 测试结果 ===")
    print(f"推荐服务测试: {'成功' if rec_success else '失败'}")
    print(f"景点过滤测试: {'成功' if filter_success else '失败'}")
    print(f"路径生成测试: {'成功' if path_success else '失败'}")
    
    if rec_success and filter_success and path_success:
        print("所有测试通过！路径优化功能正常。")
        sys.exit(0)
    else:
        print("测试失败！路径优化功能存在问题。")
        sys.exit(1)