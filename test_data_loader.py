#!/usr/bin/env python3
"""
测试data_loader模块是否能正确加载数据
"""

from app.utils.data_loader import load_weather_data, load_all_city_data
import os

print("测试load_weather_data函数...")
try:
    # 测试沈阳的天气数据加载
    city_df = load_weather_data("沈阳")
    print("✓ 成功加载沈阳的天气数据")
    print(f"  数据总行数: {len(city_df)}")
    print(f"  数据列: {list(city_df.columns)}")
    print(f"  日期范围: {city_df['日期'].min()} 到 {city_df['日期'].max()}")
    print(f"  城市: {city_df['城市'].unique()}")
except Exception as e:
    print(f"✗ 加载沈阳的天气数据失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试load_all_city_data函数...")
try:
    # 测试加载所有城市的天气数据
    all_df = load_all_city_data(use_cache=False)
    print("✓ 成功加载所有城市的天气数据")
    print(f"  数据总行数: {len(all_df)}")
    print(f"  包含城市: {all_df['城市'].unique()}")
except Exception as e:
    print(f"✗ 加载所有城市的天气数据失败: {e}")
    import traceback
    traceback.print_exc()
