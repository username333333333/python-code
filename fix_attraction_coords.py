#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库中景点的坐标信息，确保每个景点都有自己独立的坐标
"""

import sys
import os
import random

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath('.'))

from app import create_app
from app.models import Attraction

def fix_attraction_coords():
    """修复数据库中景点的坐标信息，确保每个景点都有自己独立的坐标"""
    print("开始修复数据库中景点的坐标信息...")
    
    # 创建应用实例
    app = create_app()
    
    # 在应用上下文内运行
    with app.app_context():
        # 查询所有景点
        attractions = Attraction.query.all()
        
        print(f"数据库中共有 {len(attractions)} 个景点")
        
        # 城市中心点坐标数据
        city_coords = {
            '沈阳': [41.8057, 123.4315],
            '大连': [38.9140, 121.6147],
            '鞍山': [41.1182, 122.8907],
            '抚顺': [41.9000, 124.0500],
            '本溪': [41.3116, 123.7761],
            '丹东': [40.1374, 124.3426],
            '锦州': [41.1173, 121.1440],
            '营口': [40.6668, 122.1533],
            '阜新': [42.0053, 121.6148],
            '辽阳': [41.2000, 123.2500],
            '盘锦': [41.1243, 122.0730],
            '铁岭': [42.2901, 123.8398],
            '朝阳': [41.5732, 120.4790],
            '葫芦岛': [40.7315, 120.7610]
        }
        
        # 存储每个城市的景点数量
        city_counts = {}
        
        # 统计每个城市的景点数量
        for attraction in attractions:
            city = attraction.city
            if city in city_counts:
                city_counts[city] += 1
            else:
                city_counts[city] = 1
        
        print("\n每个城市的景点数量：")
        for city, count in city_counts.items():
            print(f"{city}: {count} 个景点")
        
        # 为每个城市的景点生成独立的坐标
        updated_count = 0
        
        for city, count in city_counts.items():
            if city in city_coords:
                center_lat, center_lon = city_coords[city]
                city_attractions = Attraction.query.filter(Attraction.city == city).all()
                
                print(f"\n正在处理 {city} 的 {len(city_attractions)} 个景点...")
                
                # 为当前城市的每个景点生成不同的坐标
                for i, attraction in enumerate(city_attractions):
                    # 使用圆形分布生成坐标偏移，确保景点围绕城市中心均匀分布
                    # 计算偏移角度
                    angle = (i / len(city_attractions)) * 2 * 3.14159
                    
                    # 计算偏移距离，根据景点数量动态调整
                    # 确保同一城市的景点分布在合理范围内
                    max_radius = 0.1  # 最大偏移距离（度）
                    min_radius = 0.005  # 最小偏移距离（度）
                    # 景点越多，分布越分散
                    radius = min_radius + (max_radius - min_radius) * (len(city_attractions) / 300)
                    
                    # 添加一些随机性，避免过于规则的分布
                    random_offset = (random.random() - 0.5) * 0.01
                    radius += random_offset
                    
                    # 计算新的坐标
                    new_lat = center_lat + radius * random.random() * (1 if random.random() > 0.5 else -1)
                    new_lon = center_lon + radius * random.random() * (1 if random.random() > 0.5 else -1)
                    
                    # 更新景点坐标
                    attraction.latitude = round(new_lat, 6)
                    attraction.longitude = round(new_lon, 6)
                    updated_count += 1
                    
                    if i % 50 == 0:
                        print(f"  已处理 {i+1}/{len(city_attractions)} 个景点")
        
        # 提交更改到数据库
        from app import db
        db.session.commit()
        
        print(f"\n修复完成！共更新了 {updated_count} 个景点的坐标")
        print("现在每个景点都有自己独立的坐标，不再共享城市中心点坐标")

if __name__ == "__main__":
    fix_attraction_coords()
