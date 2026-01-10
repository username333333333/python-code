#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有景点类型偏好的推荐功能
"""

from app import create_app
from app.services.path_optimization_service import PathOptimizationService

def test_all_type_preferences():
    """测试所有景点类型偏好的推荐功能"""
    print("=" * 60)
    print("开始测试所有景点类型偏好的推荐功能...")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # 初始化服务
        path_service = PathOptimizationService()
        
        # 测试参数
        start_city = "沈阳"
        target_city = "沈阳"
        days = 2
        
        # 所有要测试的景点类型偏好
        test_types = [
            "博物馆",
            "公园",
            "风景区",
            "历史古迹",
            "自然景观"
        ]
        
        for test_type in test_types:
            print(f"\n--- 测试 {test_type} 类型偏好 ---")
            
            try:
                # 生成行程
                result = path_service.generate_closed_loop_path(
                    start_city=start_city,
                    days=days,
                    preferences={"attraction_types": [test_type], "min_rating": 0},
                    target_city=target_city,
                    selected_attractions=None
                )
                
                itinerary = result['itinerary']
                total_attractions = sum(len(day['attractions']) for day in itinerary)
                
                print(f"✅ 成功生成行程，共 {len(itinerary)} 天")
                print(f"✅ 总景点数: {total_attractions}")
                
                if total_attractions > 0:
                    print(f"✅ 推荐的前3个景点:")
                    count = 0
                    for day_plan in itinerary:
                        for attraction in day_plan['attractions']:
                            if count < 3:
                                print(f"   {count+1}. {attraction.name} - 类型: {attraction.type}, 评分: {attraction.rating}")
                                count += 1
                            else:
                                break
                        if count >= 3:
                            break
                else:
                    print(f"❌ 没有找到符合 {test_type} 类型偏好的景点")
                    
            except Exception as e:
                print(f"❌ 测试 {test_type} 类型偏好失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("所有类型偏好测试完成！")
        print("=" * 60)

if __name__ == "__main__":
    test_all_type_preferences()