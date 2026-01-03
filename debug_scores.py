import pandas as pd
import os

# 加载景点数据
data_dir = 'data'
attractions_file = os.path.join(data_dir, 'cache', 'attractions_data.pkl')
all_city_data_file = os.path.join(data_dir, 'all_city_data.pkl')

# 读取数据
attractions_df = pd.read_pickle(attractions_file)
all_city_df = pd.read_pickle(all_city_data_file)

print("=== 景点数据评分分析 ===")
# 查看景点评分数据的基本统计信息
print("景点评分统计信息：")
print(attractions_df['评分'].describe())

# 计算各城市的平均评分
city_avg_scores = attractions_df.groupby('城市')['评分'].mean().reset_index()
# 应用映射公式：(score - 1) * 25
city_avg_scores['映射后评分'] = ((city_avg_scores['评分'] - 1) * 25).round().astype(int)
# 按映射后评分排序
city_avg_scores = city_avg_scores.sort_values('映射后评分', ascending=False)
print("\n景点数据计算的城市评分（映射后）：")
print(city_avg_scores)

print("\n=== 天气数据评分分析 ===")
# 查看天气数据中的旅游评分
if '旅游评分' in all_city_df.columns:
    print("天气数据旅游评分统计信息：")
    print(all_city_df['旅游评分'].describe())
    
    # 计算各城市的平均旅游评分
    weather_city_scores = all_city_df.groupby('城市')['旅游评分'].mean().reset_index()
    weather_city_scores['旅游评分'] = weather_city_scores['旅游评分'].round().astype(int)
    weather_city_scores = weather_city_scores.sort_values('旅游评分', ascending=False)
    print("\n天气数据计算的城市平均旅游评分：")
    print(weather_city_scores)
else:
    print("天气数据中没有'旅游评分'字段")

print("\n=== 推荐指数判定标准 ===")
print("强烈推荐：>= 90 分")
print("推    荐：>= 70 分")
print("一    般：>= 50 分")
print("不推荐：< 50 分")