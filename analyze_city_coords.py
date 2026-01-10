#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析城市坐标数据，计算各城市之间的距离，识别距离过近的城市对
"""

import math

# 城市中心点坐标数据
city_coords = {
    '沈阳': [41.8057, 123.4315],
    '大连': [38.9140, 121.6147],
    '鞍山': [41.1182, 122.8907],
    '抚顺': [41.8645, 123.9506],
    '本溪': [41.3116, 123.7761],
    '丹东': [40.1374, 124.3426],
    '锦州': [41.1173, 121.1440],
    '营口': [40.6668, 122.1533],
    '阜新': [42.0053, 121.6148],
    '辽阳': [41.2641, 123.1753],
    '盘锦': [41.1243, 122.0730],
    '铁岭': [42.2901, 123.8398],
    '朝阳': [41.5732, 120.4790],
    '葫芦岛': [40.7315, 120.7610]
}

def calculate_distance(coord1, coord2):
    """
    使用Haversine公式计算两个经纬度坐标之间的距离（公里）
    
    Args:
        coord1: 第一个坐标 [lat, lon]
        coord2: 第二个坐标 [lat, lon]
        
    Returns:
        float: 两个坐标之间的距离（公里）
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # 地球半径（公里）
    R = 6371.0
    
    # 转换为弧度
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # 差异
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine公式
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance

def analyze_city_distances(city_coords, distance_threshold=50):
    """
    分析城市坐标，计算各城市之间的距离，识别距离过近的城市对
    
    Args:
        city_coords: 城市坐标字典
        distance_threshold: 距离阈值（公里），小于此值的城市对被认为是近距离
        
    Returns:
        tuple: (distances, close_city_pairs)
            distances: 所有城市对之间的距离字典
            close_city_pairs: 距离过近的城市对列表
    """
    distances = {}
    close_city_pairs = []
    
    # 获取所有城市名称
    cities = list(city_coords.keys())
    
    # 计算所有城市对之间的距离
    for i in range(len(cities)):
        for j in range(i + 1, len(cities)):
            city1 = cities[i]
            city2 = cities[j]
            coord1 = city_coords[city1]
            coord2 = city_coords[city2]
            
            distance = calculate_distance(coord1, coord2)
            
            # 存储距离
            if city1 not in distances:
                distances[city1] = {}
            distances[city1][city2] = distance
            
            # 检查是否距离过近
            if distance < distance_threshold:
                close_city_pairs.append((city1, city2, distance))
    
    # 按距离从小到大排序
    close_city_pairs.sort(key=lambda x: x[2])
    
    return distances, close_city_pairs

def print_analysis_results(distances, close_city_pairs, distance_threshold=50):
    """
    打印分析结果
    
    Args:
        distances: 所有城市对之间的距离字典
        close_city_pairs: 距离过近的城市对列表
        distance_threshold: 距离阈值（公里）
    """
    print("城市坐标距离分析报告")
    print("=" * 60)
    
    print(f"\n1. 距离阈值设置: {distance_threshold} 公里")
    
    print(f"\n2. 近距离城市对（共 {len(close_city_pairs)} 对）:")
    print("-" * 40)
    print(f"{'城市1':<8} {'城市2':<8} {'距离(公里)':<12}")
    print("-" * 40)
    for city1, city2, distance in close_city_pairs:
        print(f"{city1:<8} {city2:<8} {distance:<12.2f}")
    
    print(f"\n3. 各城市近距离邻居数量:")
    print("-" * 40)
    print(f"{'城市':<8} {'近距离邻居数':<15}")
    print("-" * 40)
    
    # 统计各城市的近距离邻居数量
    neighbor_counts = {}
    for city1, city2, _ in close_city_pairs:
        neighbor_counts[city1] = neighbor_counts.get(city1, 0) + 1
        neighbor_counts[city2] = neighbor_counts.get(city2, 0) + 1
    
    # 按邻居数量排序
    for city, count in sorted(neighbor_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{city:<8} {count:<15}")
    
    # 列出没有近距离邻居的城市
    for city in city_coords.keys():
        if city not in neighbor_counts:
            print(f"{city:<8} {0:<15}")
    
    print(f"\n4. 详细距离矩阵（仅显示非近距离）:")
    print("-" * 40)
    cities = list(city_coords.keys())
    print(f"{'':<8}", end="")
    for city in cities:
        print(f"{city:<10}", end="")
    print()
    
    for i, city1 in enumerate(cities):
        print(f"{city1:<8}", end="")
        for j, city2 in enumerate(cities):
            if i == j:
                print(f"{'—':<10}", end="")
            elif i < j:
                distance = distances[city1][city2]
                if distance < distance_threshold:
                    print(f"{'*':<10}", end="")  # 使用*标记近距离
                else:
                    print(f"{distance:<10.1f}", end="")
            else:
                # 对称矩阵，跳过
                print(f"{'':<10}", end="")
        print()
    
    print(f"\n5. 分析结论与建议:")
    print("-" * 40)
    if close_city_pairs:
        print("✓ 发现距离过近的城市对，可能导致圆弧形布局拥挤或重叠")
        print(f"✓ 建议调整这些近距离城市的坐标，或在布局时考虑特殊处理")
        print("✓ 可考虑增加距离阈值，或使用更智能的布局算法")
    else:
        print("✓ 所有城市之间的距离都大于阈值，布局应该不会出现拥挤问题")

# 执行分析
if __name__ == "__main__":
    # 设置距离阈值为50公里
    distance_threshold = 50
    distances, close_city_pairs = analyze_city_distances(city_coords, distance_threshold)
    
    # 打印分析结果
    print_analysis_results(distances, close_city_pairs, distance_threshold)
    
    # 额外分析：计算所有城市对的平均距离
    all_distances = []
    for city1 in distances:
        for city2 in distances[city1]:
            all_distances.append(distances[city1][city2])
    
    avg_distance = sum(all_distances) / len(all_distances)
    min_distance = min(all_distances)
    max_distance = max(all_distances)
    
    print(f"\n6. 统计信息:")
    print("-" * 40)
    print(f"城市总数: {len(city_coords)}")
    print(f"城市对总数: {len(all_distances)}")
    print(f"平均距离: {avg_distance:.2f} 公里")
    print(f"最小距离: {min_distance:.2f} 公里")
    print(f"最大距离: {max_distance:.2f} 公里")
