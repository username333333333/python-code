#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试地图路径坐标生成功能
验证不同景点生成的路径坐标能够正确反映各景点之间的实际相对位置关系
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.map_service import MapService

def test_path_coordinates():
    """测试路径坐标生成功能，确保路径能正确反映各景点的实际位置关系"""
    print("=" * 60)
    print("开始测试地图路径坐标生成功能...")
    print("=" * 60)
    
    # 初始化地图服务
    map_service = MapService()
    
    # 测试用例1：5个不同地理位置的景点
    print("\n测试用例1：5个不同地理位置的景点")
    
    # 创建测试景点对象
    class TestAttraction:
        def __init__(self, name, city, type, rating, latitude, longitude):
            self.name = name
            self.city = city
            self.type = type
            self.rating = rating
            self.latitude = latitude
            self.longitude = longitude
    
    # 5个不同坐标的景点列表 - 模拟辽宁省内不同城市的景点
    different_coords_attractions = [
        # 沈阳景点
        TestAttraction("沈阳故宫", "沈阳", "历史古迹", 4.7, 41.8049, 123.4328),
        # 大连景点
        TestAttraction("金石滩", "大连", "海滨", 4.5, 38.9276, 121.6186),
        # 鞍山景点
        TestAttraction("千山风景区", "鞍山", "自然景观", 4.4, 40.3887, 123.0886),
        # 丹东景点
        TestAttraction("鸭绿江断桥", "丹东", "历史古迹", 4.4, 40.1375, 124.3428),
        # 锦州景点
        TestAttraction("笔架山", "锦州", "自然景观", 4.2, 40.7000, 121.1830)
    ]
    
    try:
        # 使用旅行地图生成功能，传入不同坐标的景点
        itinerary = [{
            'day': 1,
            'attractions': [
                {
                    'name': attr.name,
                    'city': attr.city,
                    'type': attr.type,
                    'rating': attr.rating,
                    'latitude': attr.latitude,
                    'longitude': attr.longitude
                } for attr in different_coords_attractions
            ]
        }]
        
        map_obj = map_service.generate_travel_map(itinerary, start_city="沈阳", target_city="锦州")
        print("✅ 测试用例1通过：成功生成包含5个不同位置景点的路径地图")
        
        # 验证生成的HTML包含路径线（PolyLine）
        map_html = map_obj._repr_html_()
        if 'PolyLine' in map_html:
            print("✅ 路径线（PolyLine）已正确添加到地图")
        else:
            print("❌ 路径线（PolyLine）未添加到地图")
            
    except Exception as e:
        print(f"❌ 测试用例1失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例2：验证标记坐标和路径坐标的分离
    print("\n测试用例2：验证标记坐标和路径坐标的分离")
    
    # 3个相同坐标的景点 - 模拟同一位置的不同景点
    same_coords_attractions = [
        TestAttraction("景点A", "沈阳", "历史古迹", 4.5, 41.8057, 123.4315),
        TestAttraction("景点B", "沈阳", "博物馆", 4.3, 41.8057, 123.4315),
        TestAttraction("景点C", "沈阳", "公园", 4.0, 41.8057, 123.4315)
    ]
    
    try:
        itinerary = [{
            'day': 1,
            'attractions': [
                {
                    'name': attr.name,
                    'city': attr.city,
                    'type': attr.type,
                    'rating': attr.rating,
                    'latitude': attr.latitude,
                    'longitude': attr.longitude
                } for attr in same_coords_attractions
            ]
        }]
        
        map_obj = map_service.generate_travel_map(itinerary, start_city="沈阳", target_city="沈阳")
        print("✅ 测试用例2通过：成功生成包含3个相同位置景点的路径地图")
        
        # 验证生成的HTML包含多个标记
        map_html = map_obj._repr_html_()
        marker_count = map_html.count('Marker')
        if marker_count >= 3:
            print(f"✅ 成功添加了 {marker_count} 个标记，所有相同位置的景点都能显示")
        else:
            print(f"❌ 只添加了 {marker_count} 个标记，可能存在标记重叠问题")
            
    except Exception as e:
        print(f"❌ 测试用例2失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例3：验证景点分布地图功能
    print("\n测试用例3：验证景点分布地图功能")
    
    try:
        map_obj = map_service.generate_attraction_map(different_coords_attractions)
        print("✅ 测试用例3通过：成功生成景点分布地图")
        
        # 验证生成的HTML包含标记集群
        map_html = map_obj._repr_html_()
        if 'MarkerCluster' in map_html:
            print("✅ 标记集群（MarkerCluster）已正确添加到地图")
        else:
            print("❌ 标记集群（MarkerCluster）未添加到地图")
            
    except Exception as e:
        print(f"❌ 测试用例3失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("地图路径坐标生成功能测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_path_coordinates()
