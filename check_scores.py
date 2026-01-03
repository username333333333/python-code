import pandas as pd
import os
from pathlib import Path

data_dir = Path('data')
poi_dir = data_dir / 'poi'

# 获取所有景点数据文件
attraction_files = list(poi_dir.glob("*_attractions.csv"))
print(f"找到 {len(attraction_files)} 个景点数据文件")

# 加载所有数据
df_list = []
for file_path in attraction_files:
    try:
        df_city = pd.read_csv(file_path, encoding='utf-8')
        if '城市' not in df_city.columns:
            city_name = file_path.stem.split('_')[0]
            df_city['城市'] = city_name
        df_list.append(df_city)
    except Exception as e:
        print(f"加载 {file_path} 失败: {e}")
        continue

if not df_list:
    print("没有成功加载任何景点数据")
else:
    all_data = pd.concat(df_list, ignore_index=True)
    print(f"\n共加载 {len(all_data)} 个景点")
    
    # 分析评分分布
    print("\n=== 评分分布分析 ===")
    print(all_data['评分'].describe())
    
    # 分析城市平均评分
    print("\n=== 城市平均评分 ===")
    city_means = all_data.groupby('城市')['评分'].mean().sort_values(ascending=False)
    print(city_means)
    
    # 分析映射后的评分
    print("\n=== 映射后评分 (0-100) ===")
    mapped_scores = ((city_means - 1) * 25).round().astype(int)
    print(mapped_scores.sort_values(ascending=False))
    print(f"\n映射后评分的分布: {mapped_scores.describe()}")
    print(f"映射后评分的唯一值: {sorted(mapped_scores.unique())}")
    
    # 查看每个城市的推荐等级
    print("\n=== 各城市推荐等级 ===")
    for city, score in mapped_scores.items():
        if score >= 90:
            level = "强烈推荐"
        elif score >= 70:
            level = "推荐"
        elif score >= 50:
            level = "一般"
        else:
            level = "不推荐"
        print(f"{city}: {score}分 → {level}")
