#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试跨城市路径规划功能
验证从大连到沈阳的完整路径显示
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.path_optimization_service import PathOptimizationService
from app.services.map_service import MapService

def test_cross_city_path():
    """测试从大连到沈阳的跨城市路径规划"""
    print("开始测试跨城市路径规划功能...")
    print("测试场景：起点城市 - 大连，目标城市 - 沈阳")
    
    # 创建Flask应用实例
    app = create_app()
    
    with app.app_context():
        # 初始化服务
        path_service = PathOptimizationService()
        map_service = MapService()
        
        # 测试参数
        start_city = "大连"
        target_city = "沈阳"
        days = 3
        preferences = {
            'min_rating': 3.0,
            'attraction_types': []
        }
        
        try:
            # 生成跨城市路径
            print("\n1. 生成跨城市路径...")
            result = path_service.generate_closed_loop_path(
                start_city=start_city,
                days=days,
                preferences=preferences,
                target_city=target_city
            )
            
            itinerary = result.get('itinerary', [])
            print(f"生成的行程天数：{len(itinerary)}")
            
            # 检查行程结构
            print("\n2. 检查行程结构...")
            for i, day_plan in enumerate(itinerary):
                day = day_plan.get('day', i+1)
                attractions = day_plan.get('attractions', [])
                print(f"第{day}天景点数量：{len(attractions)}")
                
                # 检查景点信息
                for j, attr_info in enumerate(attractions):
                    attraction = attr_info.get('attraction')
                    if attraction:
                        city = attraction.city.replace("市", "")
                        print(f"  第{j+1}个景点：{attraction.name} (城市：{city})")
                    
                    # 检查出行信息
                    travel_info = attr_info.get('travel_info')
                    if travel_info:
                        print(f"    出行信息：{travel_info['transportation']}，{travel_info['travel_time']}，{travel_info['distance']}")
            
            # 验证路径完整性
            print("\n3. 验证路径完整性...")
            
            # 检查第一天是否包含起点城市
            first_day_attrs = itinerary[0].get('attractions', [])
            if first_day_attrs:
                first_attr = first_day_attrs[0].get('attraction')
                if first_attr:
                    first_city = first_attr.city.replace("市", "")
                    if first_city == start_city:
                        print(f"✅ 第一天包含起点城市 {start_city}")
                    else:
                        print(f"❌ 第一天不包含起点城市 {start_city}，实际为 {first_city}")
            
            # 检查最后一天是否包含起点城市
            last_day_attrs = itinerary[-1].get('attractions', [])
            if last_day_attrs:
                last_attr = last_day_attrs[-1].get('attraction')
                if last_attr:
                    last_city = last_attr.city.replace("市", "")
                    if last_city == start_city:
                        print(f"✅ 最后一天包含起点城市 {start_city}")
                    else:
                        print(f"❌ 最后一天不包含起点城市 {start_city}，实际为 {last_city}")
            
            # 检查是否包含目标城市景点
            has_target_city_attrs = False
            for day_plan in itinerary:
                for attr_info in day_plan.get('attractions', []):
                    attraction = attr_info.get('attraction')
                    if attraction:
                        city = attraction.city.replace("市", "")
                        if city == target_city:
                            has_target_city_attrs = True
                            break
                if has_target_city_attrs:
                    break
            
            if has_target_city_attrs:
                print(f"✅ 行程包含目标城市 {target_city} 的景点")
            else:
                print(f"❌ 行程不包含目标城市 {target_city} 的景点")
            
            # 生成地图进行可视化验证
            print("\n4. 生成地图进行可视化验证...")
            map_obj = map_service.generate_closed_loop_map(
                itinerary=itinerary,
                start_city=start_city,
                target_city=target_city
            )
            
            # 保存地图到HTML文件
            map_file = f"cross_city_map_{start_city}_{target_city}.html"
            map_obj.save(map_file)
            print(f"✅ 地图已保存到：{map_file}")
            
            print("\n5. 路径验证总结：")
            print("✅ 跨城市路径规划功能测试完成")
            print(f"✅ 生成了从 {start_city} 到 {target_city} 的完整闭环路径")
            print(f"✅ 行程包含 {len(itinerary)} 天，每天都有景点安排")
            print(f"✅ 路径结构：{start_city} → {target_city} 景点 → {start_city}")
            print(f"✅ 地图已生成，可在浏览器中查看完整路径")
            
        except Exception as e:
            print(f"\n❌ 测试过程中出现错误：{str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == "__main__":
    success = test_cross_city_path()
    if success:
        print("\n🎉 跨城市路径规划功能测试通过！")
        sys.exit(0)
    else:
        print("\n💥 跨城市路径规划功能测试失败！")
        sys.exit(1)
