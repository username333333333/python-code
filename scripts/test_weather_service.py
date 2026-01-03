import os
import sys
from app.services.weather_service import WeatherService

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, 'data')

# 测试WeatherService
print("测试WeatherService类...")
print(f"数据目录: {data_dir}")

# 测试沈阳天气数据
city_name = "沈阳"
print(f"\n测试加载 {city_name} 天气数据...")

weather_service = WeatherService(data_dir, city_name)
print(f"数据文件: {weather_service.data_file}")
print(f"数据行数: {len(weather_service.df)}")

# 检查日期列
if '日期' in weather_service.df.columns:
    print(f"日期列数据类型: {weather_service.df['日期'].dtype}")
    print(f"最小日期: {weather_service.df['日期'].min()}")
    print(f"最大日期: {weather_service.df['日期'].max()}")
    
    # 检查年份分布
    if hasattr(weather_service.df['日期'], 'dt'):
        print("\n年份分布:")
        year_counts = weather_service.df['日期'].dt.year.value_counts().sort_index()
        for year, count in year_counts.items():
            print(f"{year}: {count} 天")
    else:
        print("日期列不是datetime类型")
        # 打印前几行日期值
        print("前5行日期值:")
        for i in range(min(5, len(weather_service.df))):
            print(f"第{i+1}行: {weather_service.df['日期'].iloc[i]}")
else:
    print("数据中没有日期列")
    print("数据列名:")
    print(weather_service.df.columns.tolist())
