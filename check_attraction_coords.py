#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中景点的坐标信息
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath('.'))

from app import create_app
from app.models import Attraction

def check_attraction_coords():
    """检查数据库中景点的坐标信息"""
    print("开始检查数据库中景点的坐标信息...")
    
    # 创建应用实例
    app = create_app()
    
    # 在应用上下文内运行
    with app.app_context():
        # 查询所有景点
        attractions = Attraction.query.all()
        
        print(f"数据库中共有 {len(attractions)} 个景点")
        
        # 统计不同情况的景点数量
        valid_coords = 0
        null_coords = 0
        same_coords = 0
        
        # 存储所有坐标
        all_coords = []
        
        # 存储相同坐标的景点
        coords_map = {}
        
        for attraction in attractions:
            lat = attraction.latitude
            lon = attraction.longitude
            
            if lat and lon:
                valid_coords += 1
                all_coords.append((lat, lon))
                
                # 检查是否有相同坐标
                coord_key = (lat, lon)
                if coord_key in coords_map:
                    coords_map[coord_key].append(attraction)
                else:
                    coords_map[coord_key] = [attraction]
            else:
                null_coords += 1
        
        # 统计相同坐标的景点数量
        for coord_key, attrs in coords_map.items():
            if len(attrs) > 1:
                same_coords += len(attrs)
                print(f"坐标 {coord_key} 被 {len(attrs)} 个景点使用，景点名称: {[attr.name for attr in attrs]}")
        
        print(f"\n坐标统计：")
        print(f"- 有效坐标的景点数量: {valid_coords}")
        print(f"- 无效坐标的景点数量: {null_coords}")
        print(f"- 共享相同坐标的景点数量: {same_coords}")
        
        # 检查是否所有景点都使用相同的坐标
        if len(coords_map) == 1 and valid_coords > 0:
            print("\n警告：所有景点都使用相同的坐标！")
            print(f"坐标: {list(coords_map.keys())[0]}")
        
        # 查看前10个景点的坐标
        print(f"\n前10个景点的坐标信息：")
        for i, attraction in enumerate(attractions[:10], 1):
            print(f"{i}. {attraction.name} - 坐标: ({attraction.latitude}, {attraction.longitude})")

if __name__ == "__main__":
    check_attraction_coords()
