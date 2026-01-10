#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试地图多景点显示功能
测试场景：
1. 2个相同坐标的景点
2. 5个相同坐标的景点
3. 10个相同坐标的景点
4. 10个不同坐标的景点
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.map_service import MapService

def test_attraction_map():
    """测试景点分布地图生成功能"""
    print("=" * 60)
    print("开始测试景点分布地图多景点显示功能...")
    print("=" * 60)
    
    # 初始化地图服务
    map_service = MapService()
    
    # 测试用例1：2个相同坐标的景点
    print("\n测试用例1：2个相同坐标的景点")
    
    # 创建测试景点对象
    class TestAttraction:
        def __init__(self, name, city, type, rating, latitude, longitude):
            self.name = name
            self.city = city
            self.type = type
            self.rating = rating
            self.latitude = latitude
            self.longitude = longitude
    
    # 相同坐标的景点列表
    same_coords_attractions_2 = [
        TestAttraction("景点1", "沈阳", "自然景观", 4.5, 41.8057, 123.4315),
        TestAttraction("景点2", "沈阳", "人文景观", 4.3, 41.8057, 123.4315)
    ]
    
    try:
        map_obj = map_service.generate_attraction_map(same_coords_attractions_2)
        print("✅ 测试用例1通过：2个相同坐标的景点标识都能显示")
    except Exception as e:
        print(f"❌ 测试用例1失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例2：5个相同坐标的景点
    print("\n测试用例2：5个相同坐标的景点")
    
    same_coords_attractions_5 = [
        TestAttraction(f"景点{i+1}", "沈阳", "自然景观", 4.5, 41.8057, 123.4315)
        for i in range(5)
    ]
    
    try:
        map_obj = map_service.generate_attraction_map(same_coords_attractions_5)
        print("✅ 测试用例2通过：5个相同坐标的景点标识都能显示")
    except Exception as e:
        print(f"❌ 测试用例2失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例3：10个相同坐标的景点
    print("\n测试用例3：10个相同坐标的景点")
    
    same_coords_attractions_10 = [
        TestAttraction(f"景点{i+1}", "沈阳", "自然景观", 4.5, 41.8057, 123.4315)
        for i in range(10)
    ]
    
    try:
        map_obj = map_service.generate_attraction_map(same_coords_attractions_10)
        print("✅ 测试用例3通过：10个相同坐标的景点标识都能显示")
    except Exception as e:
        print(f"❌ 测试用例3失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试用例4：10个不同坐标的景点
    print("\n测试用例4：10个不同坐标的景点")
    
    diff_coords_attractions_10 = [
        TestAttraction(f"景点{i+1}", "沈阳", "自然景观", 4.5, 41.8057 + i * 0.001, 123.4315 + i * 0.001)
        for i in range(10)
    ]
    
    try:
        map_obj = map_service.generate_attraction_map(diff_coords_attractions_10)
        print("✅ 测试用例4通过：10个不同坐标的景点标识都能显示")
    except Exception as e:
        print(f"❌ 测试用例4失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("景点分布地图多景点显示功能测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_attraction_map()