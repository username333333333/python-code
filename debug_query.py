import pandas as pd
import os

# 测试数据加载和筛选功能
data_dir = 'data'

# 加载数据
print("测试数据加载...")
from app.utils.data_loader import load_all_city_data, get_filter_options

# 加载所有数据
df = load_all_city_data()
print(f"总数据行数: {len(df)}")
print(f"数据列: {list(df.columns)}")

# 检查数据前几行
print("\n数据前5行:")
print(df.head())

# 测试筛选逻辑
print("\n测试筛选逻辑...")

# 模拟空筛选条件（应该返回所有数据）
mask = pd.Series(True, index=df.index)
filtered = df[mask]
print(f"空筛选条件返回行数: {len(filtered)}")

# 测试城市筛选
city_mask = df["城市"] == "沈阳市"
filtered_city = df[city_mask]
print(f"沈阳市数据行数: {len(filtered_city)}")

# 测试天气状况筛选
weather_cols = [col for col in ['天气状况(白天)', '天气状况(夜间)'] if col in df.columns]
print(f"天气状况列: {weather_cols}")
if weather_cols:
    weather_mask = df[weather_cols[0]] == df[weather_cols[0]].iloc[0]
    filtered_weather = df[weather_mask]
    print(f"天气状况筛选返回行数: {len(filtered_weather)}")

# 检查字段名是否与模板匹配
required_cols = ['城市', '日期', '最高气温', '最低气温', '天气状况(白天)', '天气状况(夜间)', '风向(白天)', '风力(白天)_数值', '风向(夜间)', '风力(夜间)_数值']
print("\n检查模板所需字段是否存在:")
for col in required_cols:
    print(f"- {col}: {'存在' if col in df.columns else '不存在'}")

# 测试日期转换
df_copy = df.copy()
if '日期' in df_copy.columns:
    print("\n测试日期转换...")
    # 确保日期列是datetime类型
    if not pd.api.types.is_datetime64_any_dtype(df_copy['日期']):
        df_copy['日期'] = pd.to_datetime(df_copy['日期'], errors='coerce')
    # 将日期转换为字符串格式
    df_copy['日期'] = df_copy['日期'].dt.strftime('%Y-%m-%d')
    print(f"日期转换后前3行:")
    print(df_copy[['日期']].head(3))

# 测试分页
print("\n测试分页...")
page_size = 20
total_items = len(df)
total_pages = max(1, (total_items + page_size - 1) // page_size)
print(f"总页数: {total_pages}")

# 测试获取第一页数据
page = 1
start = (page - 1) * page_size
end = start + page_size
page_data = df.iloc[start:end].copy()
print(f"第1页数据行数: {len(page_data)}")

# 测试转换为字典
data_dict = page_data.to_dict(orient="records")
print(f"转换为字典后的数据数量: {len(data_dict)}")
if data_dict:
    print(f"第一条数据的键: {list(data_dict[0].keys())}")