#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为POI数据添加默认经纬度坐标脚本
使用每个城市的中心坐标作为景点的默认坐标
"""

import pandas as pd
import os
import glob

# 辽宁省城市中心坐标字典
CITY_COORDINATES = {
    '沈阳': (41.8057, 123.4315),
    '大连': (38.9140, 121.6147),
    '鞍山': (41.1182, 122.8907),
    '抚顺': (41.8645, 123.9506),
    '本溪': (41.3116, 123.7761),
    '丹东': (40.1374, 124.3426),
    '锦州': (41.1173, 121.1440),
    '营口': (40.6668, 122.1533),
    '阜新': (42.0053, 121.6148),
    '辽阳': (41.2641, 123.1753),
    '盘锦': (41.1243, 122.0730),
    '铁岭': (42.2901, 123.8398),
    '朝阳': (41.5732, 120.4790),
    '葫芦岛': (40.7315, 120.7610)
}

def add_default_coordinates():
    """为所有POI数据文件添加默认经纬度坐标"""
    print("开始为POI数据添加默认经纬度坐标...")
    
    # 获取所有POI数据文件
    poi_dir = "data/poi"
    poi_files = glob.glob(os.path.join(poi_dir, "*_attractions.csv"))
    
    for file_path in poi_files:
        file = os.path.basename(file_path)
        print(f"  处理文件: {file}")
        
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path, encoding="utf-8")
            
            # 确保列名正确
            df.columns = df.columns.str.strip()
            
            # 获取城市名称
            city = file.split('_')[0]
            
            if city in CITY_COORDINATES:
                city_lat, city_lon = CITY_COORDINATES[city]
                print(f"    使用{city}的中心坐标: ({city_lat}, {city_lon})")
                
                # 为缺失的经度和纬度添加默认值
                df['经度'] = df['经度'].fillna(city_lon)
                df['纬度'] = df['纬度'].fillna(city_lat)
                
                # 保存更新后的文件
                df.to_csv(file_path, index=False, encoding="utf-8")
                print(f"    文件{file}已更新")
            else:
                print(f"    警告: 未找到{city}的坐标信息")
                
        except Exception as e:
            print(f"    处理文件{file}时出错: {str(e)}")
    
    print("\n所有POI数据文件已处理完成！")

if __name__ == "__main__":
    add_default_coordinates()
