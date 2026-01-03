#!/usr/bin/env python3
"""
测试WeatherService是否能正确加载数据
"""

from app.services.weather_service import WeatherService
import os
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).parent
data_dir = BASE_DIR / "data"

print(f"测试数据目录: {data_dir}")

# 测试沈阳的天气数据加载
try:
    weather_service = WeatherService(data_dir, "沈阳")
    print("✓ 成功加载沈阳的天气数据")
    print(f"  数据总行数: {len(weather_service.df)}")
    print(f"  数据列: {list(weather_service.df.columns)}")
    print(f"  日期范围: {weather_service.df['日期'].min()} 到 {weather_service.df['日期'].max()}")
except Exception as e:
    print(f"✗ 加载沈阳的天气数据失败: {e}")

# 测试其他城市的天气数据加载
other_cities = ["大连", "鞍山", "本溪"]
for city in other_cities:
    try:
        weather_service = WeatherService(data_dir, city)
        print(f"✓ 成功加载{city}的天气数据")
    except Exception as e:
        print(f"✗ 加载{city}的天气数据失败: {e}")
