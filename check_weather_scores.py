import pandas as pd
import os
from pathlib import Path
from app.utils.data_loader import load_all_city_data

# 加载所有天气数据
weather_df = load_all_city_data()

print("=== 天气数据概览 ===")
print(f"数据形状: {weather_df.shape}")
print(f"列名: {list(weather_df.columns)}")

# 检查是否包含旅游评分列
if '旅游评分' in weather_df.columns:
    print("\n=== 旅游评分列分析 ===")
    print(weather_df['旅游评分'].describe())
    print(f"\n旅游评分唯一值: {sorted(weather_df['旅游评分'].unique())}")
    
    # 查看各城市的旅游评分
    print("\n=== 各城市平均旅游评分 (从weather_df) ===")
    city_scores = weather_df.groupby('城市')['旅游评分'].mean().reset_index()
    city_scores = city_scores.sort_values('旅游评分', ascending=False)
    print(city_scores)
    
    # 查看每个城市的推荐等级
    print("\n=== 各城市推荐等级 (基于weather_df) ===")
    for _, row in city_scores.iterrows():
        city = row['城市']
        score = row['旅游评分']
        if score >= 90:
            level = "强烈推荐"
        elif score >= 70:
            level = "推荐"
        elif score >= 50:
            level = "一般"
        else:
            level = "不推荐"
        print(f"{city}: {score}分 → {level}")
else:
    print("\n天气数据中不包含旅游评分列")

# 查看前几行数据
print("\n=== 数据前5行 ===")
print(weather_df.head())
