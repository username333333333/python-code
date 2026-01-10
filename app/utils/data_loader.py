import pandas as pd
import os
import re
from datetime import datetime

_cache = {
    "all_data": None,
    "options": None,
}

# 旅游出行评分权重配置
travel_score_weights = {
    "温度": 0.4,
    "天气": 0.35,
    "风力": 0.25
}

# 理想旅游天气条件
ideal_conditions = {
    "temp_range": [15, 30],  # 理想温度范围
    "ideal_weather": ['晴', '多云', '晴间多云', '多云转晴'],
    "wind_limit": 3  # 最大理想风力（级）
}

def parse_wind_power(wind_str):
    """解析风力等级字符串为数值"""
    if pd.isna(wind_str):
        return 0
    wind_str = str(wind_str).strip()
    match = re.match(r"(\d+)\s*-\s*(\d+)", wind_str)
    if match:
        low, high = match.groups()
        return (int(low) + int(high)) / 2
    match = re.search(r"(\d+)", wind_str)
    if match:
        return int(match.group(1))
    return 0

def calculate_travel_score(row):
    """计算每日旅游出行评分"""
    try:
        # 温度评分 (0-100)
        avg_temp = (row['最高气温'] + row['最低气温']) / 2
        ideal_min, ideal_max = ideal_conditions['temp_range']
        if avg_temp < ideal_min:
            temp_score = max(0, 100 - (ideal_min - avg_temp) * 5)
        elif avg_temp > ideal_max:
            temp_score = max(0, 100 - (avg_temp - ideal_max) * 5)
        else:
            temp_score = 100
        
        # 天气评分 (0-100)
        day_weather = row['天气状况(白天)']
        is_ideal = any(ideal in day_weather for ideal in ideal_conditions['ideal_weather'])
        is_acceptable = '阴' in day_weather
        is_poor = any(bad in day_weather for bad in ['雨', '雪', '雾', '霾', '沙尘暴'])
        
        if is_ideal:
            weather_score = 100
        elif is_acceptable:
            weather_score = 70
        elif is_poor:
            weather_score = 30
        else:
            weather_score = 50
        
        # 风力评分 (0-100)
        wind_power = row['风力(白天)_数值']
        if wind_power <= ideal_conditions['wind_limit']:
            wind_score = 100
        else:
            wind_score = max(0, 100 - (wind_power - ideal_conditions['wind_limit']) * 10)
        
        # 综合评分，保留整数
        total_score = (
            temp_score * travel_score_weights['温度'] +
            weather_score * travel_score_weights['天气'] +
            wind_score * travel_score_weights['风力']
        )
        
        return round(total_score)
    except Exception:
        return 0

def load_weather_data(city_name):
    """加载和预处理单个城市的天气数据"""
    # 查找数据文件，优先在weather_sensitive子目录中查找
    data_dir = "data"
    weather_sensitive_dir = os.path.join(data_dir, "weather_sensitive")
    
    possible_files = [
        # 优先在weather_sensitive子目录中查找
        os.path.join(weather_sensitive_dir, f"{city_name}2013-2023年天气数据.csv"),
        os.path.join(weather_sensitive_dir, f"{city_name}2013-2023年 天气数据.csv"),
        os.path.join(weather_sensitive_dir, f"{city_name}天气数据.csv"),
        os.path.join(weather_sensitive_dir, f"{city_name}.csv"),
        # 然后在根数据目录中查找
        os.path.join(data_dir, f"{city_name}2013-2023年天气数据.csv"),
        os.path.join(data_dir, f"{city_name}天气数据.csv"),
        os.path.join(data_dir, f"{city_name}.csv")
    ]
    
    # 查找存在的文件
    data_file = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            data_file = file_path
            break
    
    if not data_file:
        raise FileNotFoundError(f"找不到城市 {city_name} 的数据文件，请检查以下路径:\n" + "\n".join(possible_files))
    
    # 加载数据并处理日期格式
    df = pd.read_csv(data_file, encoding="utf-8", on_bad_lines='skip')
    
    # 数据质量检查和清理
    # 删除包含无效数据的行
    df = df[~df.apply(lambda row: row.astype(str).str.contains("namedStyle", case=False).any(), axis=1)]
    
    # 重命名列，处理可能的空格和错误命名
    df.columns = df.columns.str.strip()
    
    # 处理可能的列名错误，特别是天气状况列
    # 先创建一个临时映射字典，确保正确处理所有可能的列名
    column_mapping = {
        '天气 状况(白天)': '天气状况(白天)',  # 修复带空格的列名
        '天气状况(白天)': '天气状况(白天)',  # 确保正确的列名
        '天气状况(夜间)': '天气状况(夜间)',   # 确保正确的列名
        '天气 状况(夜间)': '天气状况(夜间)'   # 修复带空格的列名
    }
    
    # 只重命名实际存在的列
    actual_mapping = {}
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            actual_mapping[old_col] = new_col
    
    # 执行重命名
    if actual_mapping:
        df = df.rename(columns=actual_mapping)
    
    # 确保必要字段存在
    basic_columns = ['日期', '最高气温', '最低气温']
    for col in basic_columns:
        if col not in df.columns:
            raise ValueError(f"数据文件缺少必要列: {col}")
    
    # 再次检查和修复列名，确保所有列名都被正确处理
    # 处理可能的列名错误，特别是天气状况列
    column_mapping = {
        '天气 状况(白天)': '天气状况(白天)',  # 修复带空格的列名
        '天气状况(白天)': '天气状况(白天)',  # 确保正确的列名
        '天气 状况(夜间)': '天气状况(夜间)',  # 修复带空格的列名
        '天气状况(夜间)': '天气状况(夜间)'   # 确保正确的列名
    }
    
    # 只重命名实际存在的列
    actual_mapping = {}
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            actual_mapping[old_col] = new_col
    
    # 执行重命名
    if actual_mapping:
        df = df.rename(columns=actual_mapping)
    
    # 处理天气状况列：如果只有一个"天气状况"列，复制到白天和夜间
    if '天气状况' in df.columns:
        # 如果缺少白天和夜间的天气状况列，从"天气状况"列复制
        if '天气状况(白天)' not in df.columns:
            df['天气状况(白天)'] = df['天气状况']
        if '天气状况(夜间)' not in df.columns:
            df['天气状况(夜间)'] = df['天气状况']
    
    # 处理风力列：如果只有一个"风力"列，复制到白天和夜间
    if '风力' in df.columns:
        # 如果缺少白天和夜间的风力列，从"风力"列复制
        if '风力(白天)' not in df.columns:
            df['风力(白天)'] = df['风力']
        if '风力(夜间)' not in df.columns:
            df['风力(夜间)'] = df['风力']
    
    # 处理风向列：如果没有风向数据，添加默认值
    wind_directions = ['北风', '南风', '东风', '西风', '东北风', '东南风', '西北风', '西南风']
    
    # 为风向(白天)和风向(夜间)生成默认值
    if '风向(白天)' not in df.columns:
        # 循环使用风向列表生成数据
        df['风向(白天)'] = [wind_directions[i % len(wind_directions)] for i in range(len(df))]
    
    if '风向(夜间)' not in df.columns:
        # 循环使用风向列表生成数据
        df['风向(夜间)'] = [wind_directions[i % len(wind_directions)] for i in range(len(df))]
    
    # 确保所有必要的天气、风力和风向列存在
    required_columns = ['天气状况(白天)', '天气状况(夜间)', '风力(白天)', '风力(夜间)', '风向(白天)', '风向(夜间)']
    for col in required_columns:
        if col not in df.columns:
            df[col] = None
    
    # 删除缺失必要字段的行
    df = df.dropna(subset=['日期', '最高气温', '最低气温'])
    
    # 修复最高气温和最低气温数据反了的问题
    # 检查并交换最高气温和最低气温的值
    df['最高气温'], df['最低气温'] = df[['最高气温', '最低气温']].apply(lambda x: (x['最高气温'], x['最低气温']) if x['最高气温'] >= x['最低气温'] else (x['最低气温'], x['最高气温']), axis=1, result_type='expand').values.T
    
    # 确保日期列是datetime类型
    if '日期' in df.columns:
        # 先尝试不指定格式，让pandas自动推断
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        
        # 如果自动推断失败，尝试多种日期格式
        if df['日期'].isna().all():
            date_formats = ['%Y-%m-%d', '%Y年%m月%d日', '%m/%d/%Y', '%d/%m/%Y']
            for fmt in date_formats:
                df['日期'] = pd.to_datetime(df['日期'], format=fmt, errors='coerce')
                if not df['日期'].isna().all():
                    break
    
    # 重置索引
    df = df.reset_index(drop=True)
    
    # 添加城市名称
    df["城市"] = city_name + "市" if not city_name.endswith("市") else city_name
    
    # 解析风力数值
    df["风力(白天)_数值"] = df["风力(白天)"].apply(parse_wind_power)
    df["风力(夜间)_数值"] = df["风力(夜间)"].apply(parse_wind_power)
    
    # 添加衍生特征
    df['平均气温'] = (df['最高气温'] + df['最低气温']) / 2
    df['温差'] = df['最高气温'] - df['最低气温']
    df['月份'] = df['日期'].dt.month
    df['季节'] = df['日期'].dt.month.apply(lambda x: {
        12: '冬季', 1: '冬季', 2: '冬季',
        3: '春季', 4: '春季', 5: '春季',
        6: '夏季', 7: '夏季', 8: '夏季',
        9: '秋季', 10: '秋季', 11: '秋季'
    }[x])
    df['年份'] = df['日期'].dt.year
    df['星期'] = df['日期'].dt.day_name()
    
    # 计算旅游评分
    df['旅游评分'] = df.apply(calculate_travel_score, axis=1)
    
    # 旅游推荐标签
    df['推荐指数'] = df['旅游评分'].apply(lambda x: 
        '强烈推荐' if x >= 90 else 
        '推荐' if x >= 70 else 
        '一般' if x >= 50 else 
        '不推荐')
    
    return df

def load_all_city_data(data_dir="data", use_cache=True):
    if _cache["all_data"] is not None:
        return _cache["all_data"]
    
    # 优先从文件缓存加载数据
    cache_file = os.path.join(data_dir, "cache", "all_city_data.pkl")
    if use_cache and os.path.exists(cache_file):
        print(f"从文件缓存加载数据: {cache_file}")
        try:
            import pickle
            with open(cache_file, 'rb') as f:
                df = pickle.load(f)
            _cache["all_data"] = df
            return df
        except Exception as e:
            print(f"从文件缓存加载数据失败: {e}")
    
    print("加载本地天气数据...")
    all_data = []
    
    # 获取辽宁省所有城市名称
    liaoning_cities = [
        "沈阳", "大连", "鞍山", "抚顺", "本溪", "丹东", 
        "锦州", "营口", "阜新", "辽阳", "盘锦", "铁岭", 
        "朝阳", "葫芦岛"
    ]
    
    # 加载每个城市的天气数据
    for city in liaoning_cities:
        try:
            city_df = load_weather_data(city)
            all_data.append(city_df)
        except FileNotFoundError:
            print(f"⚠️ 无法加载 {city} 天气数据")
        except Exception as e:
            print(f"⚠️ 加载 {city} 天气数据失败: {e}")
    
    if all_data:
        df = pd.concat(all_data, ignore_index=True)
        df.reset_index(drop=True, inplace=True)
    else:
        # 无法获取数据，返回空 dataframe
        df = pd.DataFrame(columns=['日期', '城市', '最高气温', '最低气温', '天气状况(白天)', '天气状况(夜间)', '风力(白天)', '风力(夜间)'])
    
    # 保存到内存缓存
    _cache["all_data"] = df
    return df

def get_filter_options():
    if _cache["options"]:
        return _cache["options"]
    df = load_all_city_data()
    
    # 获取城市列表
    cities = sorted(df["城市"].dropna().unique()) if '城市' in df.columns else []
    
    # 获取天气状况选项
    weather_cols = [col for col in ['天气状况(白天)', '天气状况(夜间)'] if col in df.columns]
    if weather_cols:
        weather_conditions = pd.concat([df[col] for col in weather_cols], ignore_index=True)
        weather_conditions = sorted(weather_conditions.dropna().unique())
    else:
        weather_conditions = []
    
    # 获取风向选项
    wind_dir_cols = [col for col in ['风向(白天)', '风向(夜间)'] if col in df.columns]
    if wind_dir_cols:
        wind_directions = pd.concat([df[col] for col in wind_dir_cols], ignore_index=True)
        wind_directions = sorted(wind_directions.dropna().unique())
    else:
        wind_directions = []
    
    # 获取风力选项
    wind_level_cols = [col for col in ['风力(白天)', '风力(夜间)'] if col in df.columns]
    if wind_level_cols:
        wind_levels = pd.concat([df[col] for col in wind_level_cols], ignore_index=True)
        wind_levels = sorted(wind_levels.dropna().unique())
    else:
        wind_levels = []
    
    options = {
        "cities": cities,
        "weather_conditions": weather_conditions,
        "wind_directions": wind_directions,
        "wind_levels": wind_levels
    }
    _cache["options"] = options
    return options

def load_attractions_data(data_dir):
    """加载所有景点数据
    
    Args:
        data_dir: 数据目录路径
        
    Returns:
        pd.DataFrame: 所有景点数据
    """
    import glob
    
    # 获取所有poi目录下的景点数据文件
    poi_dir = os.path.join(data_dir, "poi")
    if not os.path.exists(poi_dir):
        raise ValueError(f"景点数据目录不存在: {poi_dir}")
    
    # 获取所有城市的景点数据文件
    poi_files = glob.glob(os.path.join(poi_dir, "*_attractions.csv"))
    
    all_attractions = []
    
    # 加载每个城市的景点数据
    for file_path in poi_files:
        try:
            df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines='skip')
            
            # 确保列名正确
            df.columns = df.columns.str.strip()
            
            # 重命名列名以保持一致
            column_mapping = {
                '城市': '城市',
                '景点名称': '景点名称',
                '类型': '景点类型',
                '最佳季节': '最佳季节',
                '评分': '评分',
                '门票价格': '门票价格',
                '推荐游玩时长': '推荐游玩时长',
                '简介': '简介',
                '经度': '经度',
                '纬度': '纬度',
                '电话': '电话'
            }
            
            # 只保留需要的列
            existing_cols = [col for col in column_mapping.keys() if col in df.columns]
            df = df[existing_cols]
            
            # 执行列重命名
            df = df.rename(columns=column_mapping)
            
            all_attractions.append(df)
        except Exception as e:
            print(f"加载景点数据文件失败 {file_path}: {e}")
    
    if all_attractions:
        return pd.concat(all_attractions, ignore_index=True)
    else:
        return pd.DataFrame(columns=list(column_mapping.values()))
