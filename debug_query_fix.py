import pandas as pd
import os

# 测试修复后的字段名清理功能
data_dir = 'data'

# 加载数据
from app.utils.data_loader import load_all_city_data

df = load_all_city_data()
print(f"原始数据列名: {list(df.columns)}")

# 模拟查询视图中的数据处理逻辑
page_data = df.head(5).copy()

# 清理字段名，去除空格
page_data.columns = page_data.columns.str.strip()
print(f"清理后的数据列名: {list(page_data.columns)}")

# 转换为字典
page_data_dict = page_data.to_dict(orient="records")
print(f"转换为字典后的数据键: {list(page_data_dict[0].keys())}")

# 检查模板所需字段是否都能正确获取
required_cols = ['城市', '日期', '最高气温', '最低气温', '天气状况(白天)', '天气状况(夜间)', '风向(白天)', '风力(白天)_数值', '风向(夜间)', '风力(夜间)_数值']
print("\n检查模板所需字段是否能正确获取:")
for col in required_cols:
    if col in page_data_dict[0]:
        print(f"- {col}: 可以获取，值为: {page_data_dict[0][col]}")
    else:
        print(f"- {col}: 无法获取")