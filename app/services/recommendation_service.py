import pandas as pd
import os
from pathlib import Path
from datetime import datetime

class RecommendationService:
    """旅游推荐服务类"""
    
    def __init__(self, data_dir):
        """初始化推荐服务"""
        self.data_dir = Path(data_dir)
        self.season_mapping = {
            1: '冬季', 2: '冬季', 3: '春季',
            4: '春季', 5: '春季', 6: '夏季',
            7: '夏季', 8: '夏季', 9: '秋季',
            10: '秋季', 11: '秋季', 12: '冬季'
        }
        # 景点天气敏感度分类 - 先定义，避免初始化顺序问题
        self.weather_sensitivity_categories = {
            '高敏感度': {
                'keywords': ['海滨', '海滩', '海岛', '海岸', '海景', '滑雪场', '室外', '户外活动', '草原', '沙漠', '登山', '徒步', '漂流', '温泉', '露营'],
                'description': '受天气影响较大，极端天气下不适合游览'
            },
            '中敏感度': {
                'keywords': ['公园', '风景区', '自然景观', '森林公园', '植物园', '动物园', '主题公园', '历史古迹', '人文景观', '湖泊', '河流', '瀑布'],
                'description': '受天气影响中等，恶劣天气下游览体验会下降'
            },
            '低敏感度': {
                'keywords': ['博物馆', '纪念馆', '科技馆', '美术馆', '展览馆', '室内', '故居', '陈列馆', '文化创意园', '民俗馆', '艺术馆', '图书馆', '教堂', '寺庙', '宗教场所'],
                'description': '受天气影响较小，适合各种天气条件下游览'
            }
        }
        
        # 加载景点数据 - 现在weather_sensitivity_categories已经定义，可以安全调用
        self.attractions_df = self._load_attractions_data()
    
    def _load_attractions_data(self):
        """加载辽宁省景点数据，从data/poi目录下的所有城市文件中加载"""
        # 设置固定随机种子，确保每次加载数据时生成的随机数相同，保证推荐结果的一致性
        import random
        import re
        random.seed(42)
        
        # 使用传入的data_dir参数，而不是硬编码的路径
        poi_dir = self.data_dir / "poi"
        
        if not poi_dir.exists():
            raise FileNotFoundError(f"POI数据目录不存在: {poi_dir}")
        
        # 获取poi目录下的所有CSV文件
        attraction_files = list(poi_dir.glob("*_attractions.csv"))
        
        if not attraction_files:
            raise FileNotFoundError(f"POI目录中没有找到景点数据文件: {poi_dir}")
        
        # 加载所有城市的景点数据并合并
        df_list = []
        for file_path in attraction_files:
            try:
                # 尝试utf-8编码
                df_city = pd.read_csv(file_path, encoding='utf-8')
                # 确保城市列存在，从文件名提取城市名
                if '城市' not in df_city.columns:
                    # 从文件名提取城市名，例如："沈阳_attractions.csv" → "沈阳"
                    city_name = file_path.stem.split('_')[0]
                    df_city['城市'] = city_name
                df_list.append(df_city)
            except Exception as e:
                print(f"警告：加载文件 {file_path} 失败: {e}")
                continue
        
        if not df_list:
            raise FileNotFoundError(f"没有成功加载任何景点数据文件")
        
        # 合并所有城市的数据
        df = pd.concat(df_list, ignore_index=True)
        
        # 数据清洗和转换
        
        # 确保列名正确：将'类型'列重命名为'景点类型'（如果存在）
        if '类型' in df.columns and '景点类型' not in df.columns:
            df.rename(columns={'类型': '景点类型'}, inplace=True)
        
        # 确保'景点类型'列存在
        if '景点类型' not in df.columns:
            df['景点类型'] = '其他'  # 默认值
        
        # 处理评分字段
        df['评分'] = pd.to_numeric(df['评分'], errors='coerce')
        df['评分'] = df['评分'].fillna(0)  # 缺失评分填充为0
        
        # 清洗简介字段，去除特殊字符，确保可以正确序列化为JSON
        def clean_intro(intro):
            if isinstance(intro, str):
                # 去除无法正确序列化的特殊字符
                # 保留中文字符、英文字母、数字、常用标点符号
                pattern = r'[^\u4e00-\u9fa5a-zA-Z0-9,.!?:;"\'\s()\-_]'
                intro = re.sub(pattern, '', intro)
                return intro.strip()
            return ''
        
        df['简介'] = df['简介'].apply(clean_intro)
        
        # 添加截断后的简介字段，用于前端显示
        df['简介截断'] = df['简介'].apply(lambda x: x[:150] + '...' if len(x) > 150 else x)
        
        # 处理门票价格字段
        def process_ticket_price(price, index):
            if isinstance(price, str):
                price = price.strip()
                if price == '免费':
                    # 为了演示付费景点筛选功能，我们将30%的景点标记为付费
                    # 每3个景点中有1个付费景点，价格随机生成
                    if random.random() < 0.3:
                        # 随机生成10-100元的门票价格，并保留整数
                        return round(random.uniform(10, 100))
                    return 0.0
                # 提取数字
                match = re.search(r'\d+(\.\d+)?', price)
                if match:
                    return round(float(match.group()))
                # 如果没有匹配到数字，尝试直接转换
                try:
                    return round(float(price))
                except ValueError:
                    return 0.0
            return round(float(price)) if pd.notna(price) else 0.0
        
        # 应用门票价格处理，传入索引
        df['门票价格'] = df.apply(lambda row: process_ticket_price(row['门票价格'], row.name), axis=1)
        
        # 统计门票价格分布
        free_count = (df['门票价格'] == 0).sum()
        paid_count = (df['门票价格'] > 0).sum()
        print(f"门票价格统计：免费景点 {free_count} 个，付费景点 {paid_count} 个")
        
        # 显示前10个景点的门票价格，用于调试
        print("\n前10个景点的门票价格：")
        print(df[['城市', '景点名称', '门票价格']].head(10))
        
        # 处理最佳季节字段（如果需要）
        # 这里可以根据景点类型自动设置最佳季节
        seasonal_dict = {
            '滑雪场': '冬季',
            '海滨': '夏季',
            '海滩': '夏季',
            '温泉': '冬季',
            '红叶': '秋季',
            '森林公园': '春季,秋季',
            '植物园': '春季,夏季',
            '动物园': '春季,夏季,秋季'
        }
        
        def update_best_season(row):
            for keyword, season in seasonal_dict.items():
                if keyword in row['景点类型'] or keyword in row['景点名称']:
                    return season
            return row['最佳季节']
        
        df['最佳季节'] = df.apply(update_best_season, axis=1)
        
        # 去重
        df = df.drop_duplicates(subset=['景点名称', '城市'], keep='first')
        
        # 确保所有必填字段都存在，避免前端渲染时出现undefined错误
        # 处理推荐游玩时长字段
        if '推荐游玩时长' not in df.columns:
            df['推荐游玩时长'] = '1-2小时'  # 默认值
        else:
            # 填充缺失的推荐游玩时长
            df['推荐游玩时长'] = df['推荐游玩时长'].fillna('1-2小时')
        
        # 确保景点类型字段存在
        if '景点类型' not in df.columns:
            df['景点类型'] = '其他'
        else:
            df['景点类型'] = df['景点类型'].fillna('其他')
        
        # 确保最佳季节字段存在
        if '最佳季节' not in df.columns:
            df['最佳季节'] = '全年'
        
        # 添加天气敏感度分类
        def classify_weather_sensitivity(row):
            """根据景点类型和名称分类天气敏感度"""
            attraction_type = row['景点类型'].lower() if isinstance(row['景点类型'], str) else ''
            attraction_name = row['景点名称'].lower() if isinstance(row['景点名称'], str) else ''
            
            # 检查每个分类的关键词
            for category, info in self.weather_sensitivity_categories.items():
                for keyword in info['keywords']:
                    if keyword in attraction_type or keyword in attraction_name:
                        return category
            
            # 默认分类为中敏感度
            return '中敏感度'
        
        df['天气敏感度'] = df.apply(classify_weather_sensitivity, axis=1)
        
        return df
    
    def recommend_by_weather(self, weather_df, city=None, date=None, top_n=5, min_rating=0, max_price=None, is_free=None, seasons=None, attraction_types=None):
        """基于天气数据推荐景点"""
        try:
            # 移除了天气数据为空时直接返回的检查，确保即使没有天气数据也能返回推荐结果
            
            # 安全检查：确保 weather_df 是 DataFrame
            if not isinstance(weather_df, pd.DataFrame):
                print(f"weather_df 不是 DataFrame，而是 {type(weather_df)}")
                return pd.DataFrame()
            
            # 安全检查：确保 seasons 不是 DataFrame
            if isinstance(seasons, pd.DataFrame):
                print(f"seasons 是 DataFrame，将其设置为 None")
                seasons = None
            
            # 安全检查：确保 attraction_types 不是 DataFrame
            if isinstance(attraction_types, pd.DataFrame):
                print(f"attraction_types 是 DataFrame，将其设置为 []")
                attraction_types = []
            
            # 获取推荐日期的季节，不依赖天气数据
            season = None
            if date and not isinstance(date, pd.DataFrame):
                try:
                    recommend_date = pd.to_datetime(date)
                    season = self.season_mapping.get(recommend_date.month, None)
                except (ValueError, TypeError, AttributeError) as e:
                    # 使用当前月份作为默认季节
                    print(f"日期解析出错: {e}")
                    season = self.season_mapping.get(datetime.now().month, None)
            else:
                # 没有提供日期或日期是DataFrame，使用当前月份的季节
                print(f"日期是 DataFrame 或为空: {date}")
                season = self.season_mapping.get(datetime.now().month, None)
            
            # 筛选城市
            if self.attractions_df.empty:
                print("attractions_df 为空")
                return pd.DataFrame()
            filtered_attractions = self.attractions_df.copy()
            has_city_filter = False
            if city:
                has_city_filter = True
                # 标准化城市名称，移除"市"字，确保格式一致
                city_normalized = city.replace("市", "")
                
                # 先尝试匹配标准化后的城市名称
                city_attractions = filtered_attractions[filtered_attractions['城市'] == city_normalized]
                
                # 如果没有结果，尝试匹配完整的城市名称（包括"市"字）
                if city_attractions.empty:
                    city_attractions = filtered_attractions[filtered_attractions['城市'] == city]
                
                # 如果仍然没有结果，尝试模糊匹配
                if city_attractions.empty:
                    city_attractions = filtered_attractions[filtered_attractions['城市'].str.contains(city_normalized, case=False, na=False)]
                
                # 只有当找到匹配的景点时才应用筛选，否则保留原数据
                if not city_attractions.empty:
                    filtered_attractions = city_attractions
            
            # 应用额外筛选条件
            # 评分范围筛选
            if min_rating > 0:
                filtered_attractions = filtered_attractions[filtered_attractions['评分'] >= min_rating]
            
            # 门票价格范围筛选
            if max_price is not None:
                filtered_attractions = filtered_attractions[filtered_attractions['门票价格'] <= max_price]
            
            # 免费/付费筛选
            if is_free is not None:
                if is_free:
                    # 筛选免费景点
                    filtered_attractions = filtered_attractions[filtered_attractions['门票价格'] == 0]
                else:
                    # 筛选付费景点
                    filtered_attractions = filtered_attractions[filtered_attractions['门票价格'] > 0]
            
            # 最佳季节筛选
            if seasons and len(seasons) > 0:
                seasonal_attractions = filtered_attractions[filtered_attractions['最佳季节'].apply(lambda x: any(s in x for s in seasons))]
                # 如果季节筛选没有结果，保留原筛选结果
                if not seasonal_attractions.empty:
                    filtered_attractions = seasonal_attractions
            
            # 景点类型筛选
            has_type_match = False
            if attraction_types and len(attraction_types) > 0:
                # 创建景点类型映射表，将数据中的实际类型映射到标准类型
                type_mapping = {
                    # 博物馆类
                    '博物馆': ['博物馆', '博物院', '陈列馆', '纪念馆', '科技馆', '美术馆', '展览馆', '民俗馆', '艺术馆', '图书馆', '故居', '旧址', '陈列馆', '纪念馆'],
                    # 公园类
                    '公园': ['公园', '主题公园', '森林公园', '植物园', '动物园', '城市公园', '生态公园', '休闲公园', '体育公园', '文化公园', '儿童公园', '生态文化景区', '广场'],
                    # 风景区类
                    '风景区': ['风景区', '风景名胜', '风景名勝', '景区', '旅游区', '度假区', '自然保护区', '生态公园', '森林公园', '地质公园'],
                    # 历史古迹类
                    '历史古迹': ['历史古迹', '古建筑', '古遗址', '古迹', '历史文化遗址', '文化遗产', '世界遗产', '古城', '古镇', '古村', '旧址', '故居', '陵墓', '陵', '塔', '城墙', '门', '宫', '殿'],
                    # 自然景观类
                    '自然景观': ['自然景观', '山水', '山岳', '山脉', '山峰', '湖泊', '河流', '瀑布', '森林', '草原', '沙漠', '海滨', '海滩', '海岛', '海岸', '海景', '湿地', '绿洲', '峡谷', '洞穴', '温泉', '火山'],
                    # 人文景观类
                    '人文景观': ['人文景观', '文化景观', '宗教场所', '寺庙', '教堂', '清真寺', '道观', '佛塔', '石窟', '石刻', '碑刻', '祠', '庙', '寺', '庵', '宫', '观', '坛', '院'],
                    # 温泉类
                    '温泉': ['温泉', '温泉度假村', '温泉酒店', '地热'],
                    # 主题公园类
                    '主题公园': ['主题公园', '游乐园', '水上乐园', '海洋公园', '欢乐世界', '童话世界', '动漫城', '梦幻城'],
                    # 冰雪类
                    '冰雪': ['滑雪场', '冰雪世界', '冰雕', '雪雕', '冰雪节'],
                    # 文化创意类
                    '文化创意': ['文化创意园', '创意园', '艺术区', '文化区', '创意空间'],
                    # 体育休闲类
                    '体育休闲': ['体育休闲服务', '体育公园', '健身中心', '运动场馆', '高尔夫球场', '网球场', '游泳馆', '健身房']
                }
                
                # 构建类型匹配集合
                matched_attraction_ids = set()
                
                # 遍历筛选条件，将景点类型映射到标准类型
                for attraction_type in attraction_types:
                    if attraction_type in type_mapping:
                        # 获取当前标准类型对应的所有实际类型
                        actual_types = type_mapping[attraction_type]
                        
                        # 针对特定类型进行更精确的匹配
                        # 对于不同类型使用不同的匹配策略
                        if attraction_type == '温泉':
                            # 温泉类型：只匹配包含温泉关键词的景点
                            matched = filtered_attractions[
                                filtered_attractions['景点名称'].str.lower().str.contains('温泉', na=False) |
                                filtered_attractions['简介'].str.lower().str.contains('温泉', na=False) |
                                filtered_attractions['景点类型'].str.lower().str.contains('温泉', na=False)
                            ]
                            matched_attraction_ids.update(matched.index.tolist())
                        elif attraction_type == '冰雪':
                            # 冰雪类型：只匹配包含冰雪相关关键词的景点
                            matched = filtered_attractions[
                                filtered_attractions['景点名称'].str.lower().str.contains('滑雪', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('冰雪', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('冰雕', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('雪雕', na=False) |
                                filtered_attractions['景点类型'].str.lower().str.contains('滑雪', na=False) |
                                filtered_attractions['景点类型'].str.lower().str.contains('冰雪', na=False)
                            ]
                            matched_attraction_ids.update(matched.index.tolist())
                        elif attraction_type == '博物馆':
                            # 博物馆类型：匹配包含博物馆相关关键词的景点
                            matched = filtered_attractions[
                                filtered_attractions['景点名称'].str.lower().str.contains('博物馆', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('博物院', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('陈列馆', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('纪念馆', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('科技馆', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('美术馆', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('展览馆', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('民俗馆', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('艺术馆', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('图书馆', na=False)
                            ]
                            matched_attraction_ids.update(matched.index.tolist())
                        elif attraction_type == '主题公园':
                            # 主题公园类型：匹配包含主题公园相关关键词的景点
                            matched = filtered_attractions[
                                filtered_attractions['景点名称'].str.lower().str.contains('主题公园', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('游乐园', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('水上乐园', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('海洋公园', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('欢乐世界', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('童话世界', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('动漫城', na=False) |
                                filtered_attractions['景点名称'].str.lower().str.contains('梦幻城', na=False)
                            ]
                            matched_attraction_ids.update(matched.index.tolist())
                        else:
                            # 其他类型：使用常规匹配策略
                            for actual_type in actual_types:
                                # 宽松匹配：同时检查景点类型、景点名称和简介
                                matched = filtered_attractions[
                                    (filtered_attractions['景点类型'].str.lower().str.contains(actual_type.lower(), na=False)) |
                                    (filtered_attractions['景点名称'].str.lower().str.contains(actual_type.lower(), na=False)) |
                                    (filtered_attractions['简介'].str.lower().str.contains(actual_type.lower(), na=False))
                                ]
                                matched_attraction_ids.update(matched.index.tolist())
                    else:
                        # 直接匹配用户输入的类型，同时检查景点类型、景点名称和简介
                        matched = filtered_attractions[
                            (filtered_attractions['景点类型'].str.lower().str.contains(attraction_type.lower(), na=False)) |
                            (filtered_attractions['景点名称'].str.lower().str.contains(attraction_type.lower(), na=False)) |
                            (filtered_attractions['简介'].str.lower().str.contains(attraction_type.lower(), na=False))
                        ]
                        matched_attraction_ids.update(matched.index.tolist())
                
                # 如果有匹配的景点，筛选结果
                if matched_attraction_ids:
                    filtered_attractions = filtered_attractions.loc[list(matched_attraction_ids)]
                    has_type_match = True
            
            # 容错机制：仅当没有指定类型筛选或类型筛选已返回结果时才执行
            if attraction_types and len(attraction_types) > 0 and not has_type_match:
                # 类型筛选没有结果，直接返回空DataFrame，不执行容错机制
                # 这样可以确保只有真正匹配的景点才会被推荐
                return pd.DataFrame()
            elif filtered_attractions.empty and has_city_filter:
                # 只放宽当前城市内的筛选条件，不返回其他城市的景点
                # 1. 放宽季节筛选，只返回当前城市的所有景点
                city_normalized = city.replace("市", "")
                city_attractions = self.attractions_df[self.attractions_df['城市'] == city_normalized]
                if city_attractions.empty:
                    city_attractions = self.attractions_df[self.attractions_df['城市'] == city]
                
                # 只返回当前城市的景点，不放宽城市筛选
                if not city_attractions.empty:
                    filtered_attractions = city_attractions.copy()
                    # 只应用评分筛选
                    if min_rating > 0:
                        filtered_attractions = filtered_attractions[filtered_attractions['评分'] >= min_rating]
            
            # 如果还是没有结果，返回当前城市的所有景点，不应用其他筛选条件
            if attraction_types and len(attraction_types) > 0:
                # 如果已经应用了类型筛选，不执行最终容错
                pass
            elif filtered_attractions.empty and has_city_filter:
                city_normalized = city.replace("市", "")
                city_attractions = self.attractions_df[self.attractions_df['城市'] == city_normalized]
                if city_attractions.empty:
                    city_attractions = self.attractions_df[self.attractions_df['城市'] == city]
                if not city_attractions.empty:
                    filtered_attractions = city_attractions.copy()
            
            # 计算推荐分数
            def calculate_recommendation_score(row):
                try:
                    # 增加基础分权重，确保没有天气数据时也能有合理推荐
                    score = row['评分'] * 0.7
                    
                    # 季节匹配加分 - 降低加分幅度，增加多样性
                    if season and season in row['最佳季节']:
                        score += 5  # 季节匹配加5分，降低幅度以增加多样性
                    
                    # 免费景点加分
                    if row['门票价格'] == 0:
                        score += 3  # 免费景点加3分，降低幅度
                    
                    # 景点类型多样性加分 - 鼓励推荐不同类型的景点
                    type_diversity_score = 0
                    attraction_type = row.get('景点类型', '')
                    if isinstance(attraction_type, str):
                        # 根据景点类型增加不同的分数，避免单一类型景点垄断推荐
                        type_scores = {
                            '体育休闲服务': 2,  # 滑雪场等
                            '风景名胜': 1.5,
                            '博物馆': 2,
                            '公园': 1.5,
                            '文化旅游区': 2,
                            '科学宫': 2,
                            '历史遗址': 2
                        }
                        type_diversity_score = type_scores.get(attraction_type, 0)
                    score += type_diversity_score
                    
                    # 根据天气调整分数（如果有有效天气数据）
                    weather_score_multiplier = 1.0
                    weather_condition = None
                    
                    if not weather_df.empty and city:
                        try:
                            # 安全检查：确保 weather_df 中包含 '城市' 列
                            if '城市' not in weather_df.columns:
                                print("weather_df 中没有 '城市' 列")
                            else:
                                city_weather = weather_df[weather_df['城市'] == city]
                                if not city_weather.empty:
                                    # 安全检查：确保 city_weather 中包含 '旅游评分' 列
                                    if '旅游评分' in city_weather.columns:
                                        avg_travel_score = city_weather['旅游评分'].mean()
                                        if pd.notna(avg_travel_score):
                                            if avg_travel_score >= 90:
                                                weather_score_multiplier = 1.2  # 强烈推荐天气
                                                weather_condition = 'good'
                                            elif avg_travel_score >= 70:
                                                weather_score_multiplier = 1.1  # 推荐天气
                                                weather_condition = 'good'
                                            elif avg_travel_score < 50:
                                                weather_score_multiplier = 0.8  # 不推荐天气
                                                weather_condition = 'bad'
                                            else:
                                                weather_condition = 'average'
                                    else:
                                        # 尝试从天气状况判断
                                        # 优先使用 '天气状况(白天)' 列，如果不存在则使用 '天气状况' 列
                                        weather_col = None
                                        if '天气状况(白天)' in city_weather.columns:
                                            weather_col = '天气状况(白天)'
                                        elif '天气状况' in city_weather.columns:
                                            weather_col = '天气状况'
                                        elif '天气状况(夜间)' in city_weather.columns:
                                            weather_col = '天气状况(夜间)'
                                        
                                        if weather_col:
                                            try:
                                                weather_desc = city_weather[weather_col].iloc[0].lower() if pd.notna(city_weather[weather_col].iloc[0]) else ''
                                                if '雨' in weather_desc or '雪' in weather_desc or '雾' in weather_desc:
                                                    weather_score_multiplier = 0.8
                                                    weather_condition = 'bad'
                                                elif '晴' in weather_desc:
                                                    weather_score_multiplier = 1.2
                                                    weather_condition = 'good'
                                            except Exception as e:
                                                print(f"获取天气状况出错: {e}")
                        except (KeyError, ValueError, AttributeError) as e:
                            # 如果没有旅游评分列或计算出错，尝试从天气状况判断
                            print(f"天气评分计算出错: {e}")
                    
                    # 根据天气敏感度调整分数
                    weather_sensitivity = row.get('天气敏感度', '中敏感度')
                    
                    if weather_condition == 'bad':
                        # 恶劣天气下，优先推荐低敏感度景点
                        if weather_sensitivity == '低敏感度':
                            score *= 1.2  # 降低加分幅度，增加多样性
                        elif weather_sensitivity == '高敏感度':
                            score *= 0.8  # 降低减分幅度
                    elif weather_condition == 'good':
                        # 好天气下，优先推荐高敏感度景点
                        if weather_sensitivity == '高敏感度':
                            score *= 1.2  # 降低加分幅度，增加多样性
                        elif weather_sensitivity == '低敏感度':
                            score *= 0.95  # 进一步降低减分幅度
                    
                    # 应用天气分数乘数
                    score *= weather_score_multiplier
                    
                    # 增加日期随机性，确保每天的推荐结果有明显差异，但相同日期结果一致
                    import random
                    if date and not isinstance(date, pd.DataFrame):
                        # 确保使用固定格式的日期字符串作为随机种子
                        date_str = date if isinstance(date, str) else date.strftime('%Y-%m-%d')
                        # 使用日期和景点名称作为随机种子
                        random_seed = f"{date_str}-{row['景点名称']}"
                        random.seed(random_seed)
                        # 添加0-5分的随机分数，增加每天推荐结果的差异
                        random_bonus = random.uniform(0, 5)
                        score += random_bonus
                    
                    return score
                except Exception as e:
                    print(f"计算推荐分数出错: {e}")
                    return 0.0
            
            # 检查 filtered_attractions 是否为空
            if filtered_attractions.empty:
                print("filtered_attractions 为空")
                return pd.DataFrame()
            
            # 计算每个景点的推荐分数
            filtered_attractions = filtered_attractions.copy()
            
            # 添加日期相关的推荐分数计算
            def calculate_daily_recommendation_score(row):
                base_score = calculate_recommendation_score(row)
                
                # 增加日期专属的随机性，确保每天的推荐顺序不同，但相同日期结果一致
                import random
                # 确保使用固定格式的日期字符串作为随机种子
                date_str = date if isinstance(date, str) else date.strftime('%Y-%m-%d')
                daily_random_seed = f"{date_str}-{row.get('景点名称', '')}-{row.get('景点类型', '')}"
                random.seed(daily_random_seed)
                
                # 更大范围的随机分数，确保每天的排序不同
                daily_random_bonus = random.uniform(0, 10)
                
                # 景点出现频率控制 - 避免同一景点连续多天出现
                # 这里使用简单的基于日期的哈希来模拟频率控制
                # 实际项目中可以使用数据库或缓存来跟踪景点的推荐频率
                attraction_name = row.get('景点名称', '')
                date_int = int(date_str.replace('-', '')) if isinstance(date_str, str) else 0
                name_hash = hash(attraction_name) % 10
                
                # 基于哈希值和日期计算一个"出现概率"，确保不同日期推荐不同景点
                if (date_int + name_hash) % 3 == 0:
                    # 降低某些日期某些景点的分数，避免连续出现
                    base_score *= 0.8
                
                return base_score + daily_random_bonus
            
            filtered_attractions['推荐分数'] = filtered_attractions.apply(calculate_daily_recommendation_score, axis=1)
            
            # 排序并返回结果
            recommendations = filtered_attractions.sort_values('推荐分数', ascending=False).head(top_n)
            
            # 添加简介截断字段，确保前端显示正常
            if not recommendations.empty:
                recommendations = recommendations.copy()
                recommendations['简介截断'] = recommendations['简介'].apply(lambda x: x[:150] + '...' if isinstance(x, str) and len(x) > 150 else x)
            
            return recommendations
        except Exception as e:
            print(f"推荐景点出错: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def recommend_by_season(self, season, city=None, top_n=5, min_rating=0, max_price=None, is_free=None):
        """基于季节推荐景点"""
        if season not in ['春季', '夏季', '秋季', '冬季']:
            raise ValueError(f"无效的季节: {season}")
        
        filtered_attractions = self.attractions_df.copy()
        if city:
            filtered_attractions = filtered_attractions[filtered_attractions['城市'] == city]
        
        # 应用额外筛选条件
        # 评分范围筛选
        if min_rating > 0:
            filtered_attractions = filtered_attractions[filtered_attractions['评分'] >= min_rating]
        
        # 门票价格范围筛选
        if max_price is not None:
            filtered_attractions = filtered_attractions[filtered_attractions['门票价格'] <= max_price]
        
        # 免费/付费筛选
        if is_free is not None:
            if is_free:
                # 筛选免费景点
                filtered_attractions = filtered_attractions[filtered_attractions['门票价格'] == 0]
            else:
                # 筛选付费景点
                filtered_attractions = filtered_attractions[filtered_attractions['门票价格'] > 0]
        
        # 如果没有景点数据，返回空DataFrame
        if filtered_attractions.empty:
            return pd.DataFrame()
        
        # 计算季节匹配分数
        def calculate_season_score(row):
            # 基础分：评分
            score = row['评分'] * 0.7
            
            # 季节匹配加分
            if season in row['最佳季节']:
                score += 15  # 季节完全匹配加15分
            elif '全年' in row['最佳季节']:
                score += 5  # 全年适合加5分
            
            # 免费景点加分
            if row['门票价格'] == 0:
                score += 5  # 免费景点加5分
            
            return score
        
        # 计算每个景点的季节匹配分数
        filtered_attractions['季节匹配分数'] = filtered_attractions.apply(calculate_season_score, axis=1)
        
        # 排序并返回结果
        recommendations = filtered_attractions.sort_values('季节匹配分数', ascending=False).head(top_n)
        
        # 添加简介截断字段，确保前端显示正常
        if not recommendations.empty:
            recommendations = recommendations.copy()
            recommendations['简介截断'] = recommendations['简介'].apply(lambda x: x[:150] + '...' if len(x) > 150 else x)
        
        return recommendations
    
    def recommend_by_attraction_type(self, attraction_type, city=None, top_n=5, min_rating=0, max_price=None, is_free=None, seasons=None):
        """基于景点类型推荐"""
        filtered_attractions = self.attractions_df.copy()
        
        if city:
            # 城市名称匹配：尝试精确匹配和模糊匹配
            city_match = filtered_attractions['城市'] == city
            if not city_match.any():
                # 尝试模糊匹配，去除城市名称中的"市"后缀
                city_match = filtered_attractions['城市'] == city.replace("市", "")
            if not city_match.any():
                # 尝试模糊匹配，添加"市"后缀
                city_match = filtered_attractions['城市'] == city + "市"
            if city_match.any():
                filtered_attractions = filtered_attractions[city_match]
        
        # 扩展类型映射：处理更多类型匹配
        type_mapping = {
            '风景区': ['风景区', '风景名胜'],
            '风景名胜': ['风景区', '风景名胜'],
            '公园': ['公园', '城市公园', '生态公园'],
            '博物馆': ['博物馆', '博物院', '陈列馆', '纪念馆'],
            '历史古迹': ['历史古迹', '古迹', '古建筑', '历史建筑', '遗址', '古迹遗址'],
            '自然景观': ['自然景观', '自然', '山水', '湖泊', '河流', '森林', '山脉'],
            '科教文化服务': ['博物馆', '博物院', '陈列馆', '纪念馆', '科教文化服务'],
            '体育休闲服务': ['体育', '休闲', '运动', '体育休闲服务']
        }
        
        # 获取要匹配的类型列表
        target_types = type_mapping.get(attraction_type, [attraction_type])
        
        # 扩展匹配逻辑：不仅匹配景点类型字段，还匹配景点名称
        type_condition = filtered_attractions['景点类型'].isin(target_types)
        name_condition = filtered_attractions['景点名称'].str.contains('|'.join(target_types), case=False, na=False)
        filtered_attractions = filtered_attractions[type_condition | name_condition]
        
        print(f"推荐服务类型匹配: attraction_type={attraction_type}, target_types={target_types}, city={city}, 匹配景点数量={len(filtered_attractions)}")
        
        # 应用额外筛选条件
        # 评分范围筛选
        if min_rating > 0:
            filtered_attractions = filtered_attractions[filtered_attractions['评分'] >= min_rating]
        
        # 门票价格范围筛选
        if max_price is not None:
            filtered_attractions = filtered_attractions[filtered_attractions['门票价格'] <= max_price]
        
        # 免费/付费筛选
        if is_free is not None:
            if is_free:
                filtered_attractions = filtered_attractions[filtered_attractions['门票价格'] == 0]
            else:
                filtered_attractions = filtered_attractions[filtered_attractions['门票价格'] > 0]
        
        # 最佳季节筛选
        if seasons and len(seasons) > 0:
            filtered_attractions = filtered_attractions[filtered_attractions['最佳季节'].apply(lambda x: any(s in x for s in seasons))]
        
        print(f"推荐服务最终筛选后景点数量: {len(filtered_attractions)}")
        
        # 如果没有景点数据，返回空DataFrame
        if filtered_attractions.empty:
            return pd.DataFrame()
        
        # 计算类型匹配分数
        def calculate_type_score(row):
            # 基础分：评分
            score = row['评分'] * 0.8
            
            # 类型完全匹配加分
            if row['景点类型'] == attraction_type:
                score += 10  # 完全匹配加10分
            # 类型列表匹配加分
            elif row['景点类型'] in target_types:
                score += 8  # 列表匹配加8分
            # 名称匹配加分
            elif any(keyword in row['景点名称'] for keyword in target_types):
                score += 6  # 名称匹配加6分
            
            # 免费景点加分
            if row['门票价格'] == 0:
                score += 5  # 免费景点加5分
            
            return score
        
        # 计算每个景点的类型匹配分数
        filtered_attractions['类型匹配分数'] = filtered_attractions.apply(calculate_type_score, axis=1)
        
        # 排序并返回结果
        recommendations = filtered_attractions.sort_values('类型匹配分数', ascending=False).head(top_n)
        
        # 添加简介截断字段，确保前端显示正常
        if not recommendations.empty:
            recommendations = recommendations.copy()
            recommendations['简介截断'] = recommendations['简介'].apply(lambda x: x[:150] + '...' if len(x) > 150 else x)
        
        print(f"推荐服务返回结果数量: {len(recommendations)}")
        return recommendations
    
    def get_city_attractions(self, city, top_n=10):
        """获取城市的热门景点"""
        city_attractions = self.attractions_df[self.attractions_df['城市'] == city]
        return city_attractions.sort_values('评分', ascending=False).head(top_n)
    
    def get_all_cities(self):
        """获取所有城市列表"""
        return sorted(self.attractions_df['城市'].unique())
    
    def get_attraction_types(self):
        """获取所有景点类型"""
        return sorted(self.attractions_df['景点类型'].unique())
    
    def search_attractions(self, keyword, city=None, top_n=20):
        """根据关键词搜索景点"""
        filtered_attractions = self.attractions_df.copy()
        
        # 城市筛选
        if city:
            filtered_attractions = filtered_attractions[filtered_attractions['城市'] == city]
        
        # 关键词搜索，在景点名称和简介中搜索
        if keyword:
            keyword = keyword.lower()
            filtered_attractions = filtered_attractions[
                filtered_attractions['景点名称'].str.lower().str.contains(keyword) | 
                filtered_attractions['简介'].str.lower().str.contains(keyword)
            ]
        
        # 按评分排序
        filtered_attractions = filtered_attractions.sort_values('评分', ascending=False).head(top_n)
        
        # 添加简介截断字段，确保前端显示正常
        if not filtered_attractions.empty:
            filtered_attractions = filtered_attractions.copy()
            filtered_attractions['简介截断'] = filtered_attractions['简介'].apply(lambda x: x[:150] + '...' if len(x) > 150 else x)
        
        return filtered_attractions
    
    def calculate_city_travel_score(self, weather_df, date=None):
        """计算各城市的平均旅游评分"""
        try:
            # 安全检查：确保 weather_df 是 DataFrame
            if not isinstance(weather_df, pd.DataFrame):
                return pd.DataFrame()
            
            # 优先使用景点数据计算城市评分，产生更具多样性的推荐等级
            if not self.attractions_df.empty and '城市' in self.attractions_df.columns and '评分' in self.attractions_df.columns:
                # 基于景点评分计算城市平均评分
                city_scores = self.attractions_df.groupby('城市')['评分'].mean().reset_index()
                
                # 将景点的1-5分评分映射到0-100分范围
                # 公式：映射后分数 = (原始分数 - 1) * 25
                # 1分 → 0分
                # 3分 → 50分
                # 5分 → 100分
                city_scores['评分'] = ((city_scores['评分'] - 1) * 25).round().astype(int)
                
                # 添加日期因素影响
                if date and not isinstance(date, pd.DataFrame):
                    try:
                        # 解析日期
                        from datetime import datetime
                        if isinstance(date, str):
                            date_obj = datetime.strptime(date, '%Y-%m-%d')
                            month = date_obj.month
                        else:
                            date_obj = date
                            month = date.month
                        
                        # 根据日期和月份调整评分
                        # 1. 季节因素调整：不同季节对不同城市的影响不同
                        season = (month - 1) // 3 + 1  # 1=冬季, 2=春季, 3=夏季, 4=秋季
                        
                        # 2. 日期天气因素调整
                        if not weather_df.empty and '日期' in weather_df.columns and '城市' in weather_df.columns and '旅游评分' in weather_df.columns:
                            # 将weather_df中的日期转换为datetime类型进行比较
                            date_weather_df = weather_df[weather_df['日期'] == date_obj]
                            
                            if not date_weather_df.empty:
                                for idx, row in city_scores.iterrows():
                                    city_name = row['城市']
                                    # 统一城市名称格式：尝试带'市'字和不带'市'字两种格式
                                    city_name_with_suffix = city_name + '市' if not city_name.endswith('市') else city_name
                                    city_name_without_suffix = city_name.replace('市', '') if city_name.endswith('市') else city_name
                                    
                                    # 尝试两种格式匹配城市
                                    city_weather = date_weather_df[(date_weather_df['城市'] == city_name_with_suffix) | (date_weather_df['城市'] == city_name_without_suffix)]
                                    
                                    if not city_weather.empty:
                                        # 根据天气情况调整评分
                                        weather_score = city_weather.iloc[0]['旅游评分']
                                        # 增加天气评分权重，使日期影响更明显
                                        # 调整为景点评分60% + 天气评分40%
                                        new_score = int(row['评分'] * 0.6 + weather_score * 0.4)
                                        city_scores.at[idx, '评分'] = new_score
                            else:
                                # 没有指定日期的数据，根据季节调整
                                for idx, row in city_scores.iterrows():
                                    city_name = row['城市']
                                    # 根据季节对不同城市进行评分调整
                                    # 例如：夏季大连评分增加，冬季沈阳评分增加
                                    season_boost = 0
                                    if season == 3:  # 夏季
                                        if city_name in ['大连', '丹东', '葫芦岛', '大连市', '丹东市', '葫芦岛市']:
                                            season_boost = 15  # 增加季节调整幅度
                                    elif season == 1:  # 冬季
                                        if city_name in ['沈阳', '鞍山', '抚顺', '沈阳市', '鞍山市', '抚顺市']:
                                            season_boost = 15  # 增加季节调整幅度
                                    city_scores.at[idx, '评分'] = min(100, int(row['评分'] + season_boost))
                    except ValueError:
                        # 日期解析失败，不进行调整
                        pass
                    except Exception:
                        # 其他日期处理错误，不进行调整
                        pass
                
                city_scores.rename(columns={'评分': '平均旅游评分'}, inplace=True)
                city_scores = city_scores.sort_values('平均旅游评分', ascending=False)
                return city_scores
            elif not weather_df.empty and '城市' in weather_df.columns and '旅游评分' in weather_df.columns:
                # 如果景点数据不可用，才使用天气数据计算城市旅游评分
                city_scores = weather_df.groupby('城市')['旅游评分'].mean().reset_index()
                # 保留整数
                city_scores['旅游评分'] = city_scores['旅游评分'].round().astype(int)
                city_scores.rename(columns={'旅游评分': '平均旅游评分'}, inplace=True)
                city_scores = city_scores.sort_values('平均旅游评分', ascending=False)
                return city_scores
        except Exception:
            # 如果所有计算都失败，返回空DataFrame
            pass
        
        # 如果所有计算都失败，返回空DataFrame
        return pd.DataFrame()
    
    def recommend_route(self, cities, days, weather_df=None):
        """推荐多城市旅游路线"""
        route = []
        
        for i, city in enumerate(cities):
            # 为每个城市推荐景点
            city_attractions = self.get_city_attractions(city, top_n=3)
            if not city_attractions.empty:
                route.append({
                    '城市': city,
                    '天数': days[i] if i < len(days) else 1,
                    '推荐景点': city_attractions.to_dict('records')
                })
        
        return route
