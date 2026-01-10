#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在Flask应用上下文中测试路径优化功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

# 导入Flask应用
from app import create_app

# 创建Flask应用实例
app = create_app()

# 在应用上下文中测试路径优化功能
with app.app_context():
    from app.services.path_optimization_service import PathOptimizationService
    from app.services.recommendation_service import RecommendationService
    
    print("=== 在Flask应用上下文中测试路径优化功能 ===")
    
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
        
        success = False
        for i, day_plan in enumerate(itinerary):
            print(f"\n第{i+1}天景点数量: {len(day_plan['attractions'])}")
            if len(day_plan['attractions']) > 0:
                success = True
            for attr_info in day_plan['attractions']:
                attr = attr_info['attraction'] if isinstance(attr_info, dict) and 'attraction' in attr_info else attr_info
                print(f"  - {attr.name} ({attr.city}, {attr.type}, {attr.rating})")
        
        print(f"\n=== 测试结果 ===")
        if success:
            print("路径优化功能测试成功！")
            sys.exit(0)
        else:
            print("路径优化功能测试失败！没有生成景点。")
            sys.exit(1)
            
    except Exception as e:
        print(f"路径优化服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)