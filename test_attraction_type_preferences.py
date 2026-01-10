#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试景点类型偏好推荐功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath('.'))

from app import create_app
from app.services.path_optimization_service import PathOptimizationService

def test_attraction_type_preferences():
    """测试不同景点类型偏好下的推荐结果"""
    print("开始测试景点类型偏好推荐功能...")
    
    # 创建应用实例
    app = create_app()
    
    # 在应用上下文内运行测试
    with app.app_context():
        # 初始化路径优化服务
        path_service = PathOptimizationService()
        
        # 测试参数
        start_city = "沈阳"
        target_city = "沈阳"
        
        # 不同类型偏好的测试用例
        test_cases = [
            {"name": "风景区", "types": ["风景区"]},
            {"name": "公园", "types": ["公园"]},
            {"name": "博物馆", "types": ["博物馆"]},
            {"name": "风景名胜", "types": ["风景名胜"]}
        ]
        
        # 存储每个测试用例的推荐结果
        results = {}
        
        for test_case in test_cases:
            print(f"\n--- 测试 {test_case['name']} 类型偏好 ---")
            
            # 构造偏好参数
            preferences = {
                "attraction_types": test_case["types"],
                "min_rating": 0
            }
            
            # 获取推荐景点
            attractions = path_service._filter_attractions(preferences, start_city, target_city)
            
            print(f"推荐景点数量: {len(attractions)}")
            
            # 存储结果
            results[test_case['name']] = {
                "count": len(attractions),
                "attractions": [f"{attr.name} ({attr.type})" for attr in attractions[:5]]  # 只存储前5个
            }
            
            # 打印前5个推荐景点
            print("前5个推荐景点:")
            for i, attr in enumerate(attractions[:5], 1):
                print(f"{i}. {attr.name} - 类型: {attr.type}, 评分: {attr.rating}")
        
        # 比较结果，检查是否有差异
        print("\n--- 结果比较 ---")
        all_same = True
        first_result = None
        
        for case_name, result in results.items():
            print(f"{case_name}: {result['count']}个景点")
            
            if first_result is None:
                first_result = result
            else:
                # 检查景点数量是否不同
                if result['count'] != first_result['count']:
                    all_same = False
                # 检查前5个景点是否完全相同
                elif result['attractions'] != first_result['attractions']:
                    all_same = False
        
        if all_same:
            print("\n❌ 测试失败：不同类型偏好返回相同结果")
            return False
        else:
            print("\n✅ 测试成功：不同类型偏好返回不同结果")
            return True

if __name__ == "__main__":
    success = test_attraction_type_preferences()
    sys.exit(0 if success else 1)
