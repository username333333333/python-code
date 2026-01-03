from app.utils.data_loader import load_all_city_data, load_attractions_data
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from datetime import datetime, timedelta
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrafficPredictionService:
    """客流量预测服务
    
    基于历史天气数据和景点属性，构建客流量预测模型，支持节假日和极端天气下的客流量预测
    """
    
    def __init__(self, data_dir):
        """初始化服务
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.models = {}  # 存储按景点训练的模型
        try:
            self.attractions_df = load_attractions_data(data_dir)
            logger.info(f"成功加载景点数据，共 {len(self.attractions_df)} 个景点")
        except Exception as e:
            logger.error(f"加载景点数据失败: {str(e)}")
            self.attractions_df = pd.DataFrame()  # 返回空数据框，避免后续操作失败
        
    def _is_holiday(self, date):
        """判断日期是否为节假日
        
        Args:
            date: 日期对象或字符串
            
        Returns:
            bool: 是否为节假日
        """
        # 转换为日期对象
        if isinstance(date, str):
            date = pd.to_datetime(date)
        
        # 获取月份和日期
        month = date.month
        day = date.day
        year = date.year
        
        # 中国主要节假日（固定日期）
        fixed_holidays = {
            (1, 1): True,  # 元旦
            (5, 1): True,  # 劳动节
            (5, 2): True,  # 劳动节
            (5, 3): True,  # 劳动节
            (10, 1): True,  # 国庆节
            (10, 2): True,  # 国庆节
            (10, 3): True,  # 国庆节
            (10, 4): True,  # 国庆节
            (10, 5): True,  # 国庆节
            (10, 6): True,  # 国庆节
            (10, 7): True,  # 国庆节
        }
        
        # 春节（每年农历正月初一，这里使用公历近似日期）
        # 添加更多年份的春节日期
        spring_festival = {
            2023: (1, 22),
            2024: (2, 10),
            2025: (1, 29),
            2026: (2, 17),
            2027: (2, 6),
            2028: (1, 26),
            2029: (2, 13),
            2030: (2, 3)
        }
        
        # 清明节（每年公历4月4日或5日）
        tomb_sweeping_day = {
            2023: (4, 5),
            2024: (4, 4),
            2025: (4, 4),
            2026: (4, 5),
            2027: (4, 5),
            2028: (4, 4),
            2029: (4, 4),
            2030: (4, 5)
        }
        
        # 端午节（每年农历五月初五，公历近似日期）
        dragon_boat_festival = {
            2023: (6, 22),
            2024: (6, 10),
            2025: (5, 31),
            2026: (6, 19),
            2027: (6, 9),
            2028: (5, 28),
            2029: (6, 16),
            2030: (6, 5)
        }
        
        # 中秋节（每年农历八月十五，公历近似日期）
        mid_autumn_festival = {
            2023: (9, 29),
            2024: (9, 17),
            2025: (10, 6),
            2026: (9, 25),
            2027: (9, 15),
            2028: (10, 3),
            2029: (9, 22),
            2030: (9, 12)
        }
        
        # 检查是否为固定节假日
        if (month, day) in fixed_holidays:
            return True
        
        # 检查是否为春节期间（初一至初六）
        if year in spring_festival:
            sf_month, sf_day = spring_festival[year]
            sf_date = pd.Timestamp(year=year, month=sf_month, day=sf_day)
            # 春节期间：初一至初六
            if sf_date <= date <= sf_date + pd.Timedelta(days=5):
                return True
        
        # 检查是否为清明节
        if year in tomb_sweeping_day:
            tsd_month, tsd_day = tomb_sweeping_day[year]
            tsd_date = pd.Timestamp(year=year, month=tsd_month, day=tsd_day)
            # 清明节前后各一天
            if tsd_date - pd.Timedelta(days=1) <= date <= tsd_date + pd.Timedelta(days=1):
                return True
        
        # 检查是否为端午节
        if year in dragon_boat_festival:
            dbf_month, dbf_day = dragon_boat_festival[year]
            dbf_date = pd.Timestamp(year=year, month=dbf_month, day=dbf_day)
            # 端午节当天
            if date == dbf_date:
                return True
        
        # 检查是否为中秋节
        if year in mid_autumn_festival:
            maf_month, maf_day = mid_autumn_festival[year]
            maf_date = pd.Timestamp(year=year, month=maf_month, day=maf_day)
            # 中秋节当天
            if date == maf_date:
                return True
        
        # 检查是否为周末
        if date.weekday() >= 5:
            return True
        
        return False
    
    def _prepare_training_data(self, attraction_name):
        """准备训练数据
        
        Args:
            attraction_name: 景点名称
            
        Returns:
            tuple: (X_train, X_test, y_train, y_test) 训练和测试数据
        """
        # 加载所有天气数据
        weather_df = load_all_city_data()
        
        try:
            # 尝试精确匹配景点名称
            attraction = self.attractions_df[self.attractions_df['景点名称'] == attraction_name]
            
            if attraction.empty:
                # 如果精确匹配失败，尝试模糊匹配
                attraction = self.attractions_df[self.attractions_df['景点名称'].str.contains(attraction_name, na=False)]
                
                if attraction.empty:
                    # 如果模糊匹配也失败，返回第一个景点作为默认值
                    if not self.attractions_df.empty:
                        attraction = self.attractions_df.head(1)
                    else:
                        raise ValueError(f"景点 {attraction_name} 不存在，且没有默认景点数据")
        except Exception as e:
            # 如果出现任何错误，返回第一个景点作为默认值
            if not self.attractions_df.empty:
                attraction = self.attractions_df.head(1)
            else:
                raise ValueError(f"景点 {attraction_name} 不存在，且没有默认景点数据")
        
        city = attraction.iloc[0]['城市']
        attraction_type = attraction.iloc[0]['类型']
        
        # 筛选该城市的天气数据
        city_weather = weather_df[weather_df['城市'] == city].copy()
        
        # 如果没有该城市的数据，生成一些模拟数据
        if city_weather.empty:
            # 生成365天的模拟天气数据
            dates = pd.date_range(start='2023-01-01', periods=365, freq='D')
            
            # 生成随机天气数据
            import numpy as np
            # 使用当前时间作为随机种子，确保每次运行结果不同
            np.random.seed(int(datetime.now().timestamp()))
            
            # 随机生成天气状况
            weather_conditions = ['晴', '多云', '阴', '雨', '雪', '雾']
            
            # 创建模拟数据
            city_weather = pd.DataFrame({
                '日期': dates,
                '城市': city,
                '最高气温': np.random.randint(-10, 35, 365),
                '最低气温': np.random.randint(-20, 25, 365),
                '天气状况(白天)': np.random.choice(weather_conditions, 365),
                '天气状况(夜间)': np.random.choice(weather_conditions, 365),
                '风力(白天)': np.random.choice([1.5, 3.5, 5.5], 365),  # 使用数值而不是字符串
                '风力(夜间)': np.random.choice([1.5, 3.5, 5.5], 365),  # 使用数值而不是字符串
                '风向(白天)': np.random.choice(['北风', '南风', '东风', '西风'], 365),
                '风向(夜间)': np.random.choice(['北风', '南风', '东风', '西风'], 365)
            })
        
        # 计算客流量（这里使用模拟数据，实际应该从数据库或文件中加载）
        # 客流量 = 基础客流量 * 天气系数 * 季节系数 * 类型系数 * 节假日系数
        base_traffic = 1000  # 基础客流量
        
        # 天气系数
        weather_coef = {
            '晴': 1.2,
            '多云': 1.0,
            '阴': 0.8,
            '雨': 0.5,
            '雪': 0.3,
            '雾': 0.6
        }
        
        # 季节系数
        season_coef = {
            '春季': 1.1,
            '夏季': 1.3,
            '秋季': 1.2,
            '冬季': 0.8
        }
        
        # 景点类型系数
        type_coef = {
            '博物馆': 1.0,
            '公园': 1.2,
            '风景区': 1.3,
            '历史古迹': 0.9,
            '自然景观': 1.4,
            '人文景观': 1.1,
            '主题公园': 1.5,
            '温泉': 1.0,
            '海滨': 1.4
        }
        
        # 节假日系数
        holiday_coef = 1.5  # 节假日客流量系数
        
        # 生成模拟客流量数据
        city_weather['客流量'] = base_traffic
        
        # 应用天气系数
        city_weather['天气系数'] = city_weather['天气状况(白天)'].apply(
            lambda x: max(weather_coef.get(x, 0.7), 0.1)
        )
        
        # 应用季节系数
        city_weather['月份'] = pd.to_datetime(city_weather['日期']).dt.month
        city_weather['季节'] = city_weather['月份'].apply(
            lambda x: '春季' if 3 <= x <= 5 else 
                     '夏季' if 6 <= x <= 8 else 
                     '秋季' if 9 <= x <= 11 else '冬季'
        )
        city_weather['季节系数'] = city_weather['季节'].apply(
            lambda x: season_coef.get(x, 1.0)
        )
        
        # 应用景点类型系数
        type_factor = type_coef.get(attraction_type, 1.0)
        
        # 应用节假日系数
        city_weather['是否节假日'] = city_weather['日期'].apply(self._is_holiday)
        city_weather['节假日系数'] = city_weather['是否节假日'].apply(lambda x: holiday_coef if x else 1.0)
        
        # 计算最终客流量
        city_weather['客流量'] = city_weather['客流量'] * city_weather['天气系数'] * city_weather['季节系数'] * type_factor * city_weather['节假日系数']
        
        # 添加随机波动
        import numpy as np
        # 使用当前时间作为随机种子，确保每次运行结果不同
        np.random.seed(int(datetime.now().timestamp()))
        city_weather['客流量'] = city_weather['客流量'] * (0.8 + np.random.rand(len(city_weather)) * 0.4)
        city_weather['客流量'] = city_weather['客流量'].astype(int)
        
        # 确保至少有一些数据行
        if len(city_weather) < 10:
            # 如果数据太少，复制现有数据行以增加样本量
            city_weather = pd.concat([city_weather] * 10, ignore_index=True)
        
        # 确保风力列是数值类型
        if '风力(白天)' in city_weather.columns:
            if isinstance(city_weather['风力(白天)'].iloc[0], str):
                # 解析风力字符串为数值
                from app.utils.data_loader import parse_wind_power
                city_weather['风力(白天)_数值'] = city_weather['风力(白天)'].apply(parse_wind_power)
            else:
                city_weather['风力(白天)_数值'] = city_weather['风力(白天)']
        else:
            # 如果没有风力数据，生成默认值
            import numpy as np
            city_weather['风力(白天)_数值'] = np.random.randint(1, 7, len(city_weather))
        
        # 确保降水量列存在
        if '降水量' not in city_weather.columns:
            # 根据天气状况生成合理的降水量
            def generate_precipitation(weather):
                if '雨' in weather:
                    return random.randint(5, 50)
                elif '雪' in weather:
                    return random.randint(0, 30)
                else:
                    return 0
            
            import random
            city_weather['降水量'] = city_weather['天气状况(白天)'].apply(generate_precipitation)
        
        # 确保平均气温列存在
        if '平均气温' not in city_weather.columns:
            city_weather['平均气温'] = (city_weather['最高气温'] + city_weather['最低气温']) / 2
        
        # 特征工程 - 添加更多相关特征
        # 添加星期几特征
        city_weather['星期'] = pd.to_datetime(city_weather['日期']).dt.dayofweek
        
        # 添加是否为周末特征
        city_weather['是否周末'] = city_weather['星期'].apply(lambda x: 1 if x >= 5 else 0)
        
        # 添加极端天气标记
        def is_extreme_weather(row):
            # 极端高温 (>35°C)
            if row['最高气温'] > 35:
                return 1
            # 极端低温 (<-10°C)
            elif row['最低气温'] < -10:
                return 1
            # 暴雨 (>30mm)
            elif row['降水量'] > 30:
                return 1
            # 大暴雨 (>50mm)
            elif row['降水量'] > 50:
                return 1
            # 特大暴雨 (>100mm)
            elif row['降水量'] > 100:
                return 1
            # 大风 (>6级)
            elif row['风力(白天)_数值'] > 6:
                return 1
            # 台风 (>12级)
            elif row['风力(白天)_数值'] > 12:
                return 1
            # 雾 (<1000m能见度)
            elif '雾' in row['天气状况(白天)'] or '霾' in row['天气状况(白天)']:
                return 1
            # 强雷电
            elif '雷' in row['天气状况(白天)'] or '电' in row['天气状况(白天)']:
                return 1
            else:
                return 0
        
        city_weather['极端天气'] = city_weather.apply(is_extreme_weather, axis=1)
        
        # 添加节假日特征
        city_weather['是否节假日'] = city_weather['是否节假日'].astype(int)
        
        # 使用更多相关特征，包括节假日特征
        features = ['最高气温', '最低气温', '平均气温', '降水量', '风力(白天)_数值', '月份', '星期', '是否周末', '是否节假日', '极端天气']
        X = city_weather[features]
        y = city_weather['客流量']
        
        # 分割训练集和测试集
        return train_test_split(X, y, test_size=0.2, random_state=42)
    
    def _train_model(self, X_train, y_train):
        """训练模型
        
        Args:
            X_train: 训练特征
            y_train: 训练标签
            
        Returns:
            model: 训练好的模型
        """
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        return model
    
    def train_all_models(self):
        """训练所有景点的客流量预测模型
        
        Returns:
            dict: 训练结果，包含每个景点的模型和评估指标
        """
        training_results = {}
        attraction_names = self.attractions_df['景点名称'].unique()
        logger.info(f"开始训练 {len(attraction_names)} 个景点的客流量预测模型")
        
        # 遍历所有景点
        for i, attraction_name in enumerate(attraction_names):
            try:
                logger.info(f"正在训练第 {i+1}/{len(attraction_names)} 个景点: {attraction_name}")
                # 准备训练数据
                X_train, X_test, y_train, y_test = self._prepare_training_data(attraction_name)
                logger.debug(f"为 {attraction_name} 准备了 {len(X_train)} 个训练样本和 {len(X_test)} 个测试样本")
                
                # 训练模型
                model = self._train_model(X_train, y_train)
                
                # 评估模型
                y_pred = model.predict(X_test)
                mse = mean_squared_error(y_test, y_pred)
                rmse = mse ** 0.5
                
                # 保存模型
                self.models[attraction_name] = model
                
                # 保存训练结果
                training_results[attraction_name] = {
                    'mse': mse,
                    'rmse': rmse,
                    'samples': len(X_train) + len(X_test)
                }
                logger.info(f"成功训练 {attraction_name} 模型，MSE: {mse:.2f}, RMSE: {rmse:.2f}")
            except Exception as e:
                error_msg = str(e)
                training_results[attraction_name] = {
                    'error': error_msg
                }
                logger.error(f"训练 {attraction_name} 模型失败: {error_msg}")
        
        logger.info(f"模型训练完成，成功训练 {len([r for r in training_results.values() if 'error' not in r])} 个模型，失败 {len([r for r in training_results.values() if 'error' in r])} 个模型")
        return training_results
    
    def predict_traffic(self, attraction_name, weather_df, is_holiday=False):
        """预测景点客流量
        
        Args:
            attraction_name: 景点名称
            weather_df: 天气数据
            is_holiday: 是否为节假日
            
        Returns:
            tuple: (预测的客流量, 客流量变化原因)
        """
        if attraction_name not in self.models:
            # 如果模型不存在，训练模型
            X_train, X_test, y_train, y_test = self._prepare_training_data(attraction_name)
            model = self._train_model(X_train, y_train)
            self.models[attraction_name] = model
        
        model = self.models[attraction_name]
        
        # 准备特征数据 - 使用与训练时相同的特征列表
        features = ['最高气温', '最低气温', '平均气温', '降水量', '风力(白天)_数值', '月份', '星期', '是否周末', '是否节假日', '极端天气']
        X = weather_df[features]
        
        # 预测基础客流量
        base_prediction = model.predict(X)[0]
        prediction = base_prediction
        
        # 客流量变化原因
        change_reason = []
        
        # 节假日客流量调整
        if is_holiday:
            holiday_factor = 1.3
            prediction = prediction * holiday_factor
            change_reason.append(f"节假日影响，客流量增加 {int((holiday_factor - 1) * 100)}%")
        
        # 极端天气客流量调整
        if weather_df['极端天气'].iloc[0] == 1:
            # 根据不同的极端天气类型进行调整
            max_temp = weather_df['最高气温'].iloc[0]
            min_temp = weather_df['最低气温'].iloc[0]
            precipitation = weather_df['降水量'].iloc[0]
            wind_power = weather_df['风力(白天)_数值'].iloc[0]
            
            extreme_factor = 0.5  # 默认极端天气系数
            extreme_type = "极端天气"
            
            if max_temp > 35:
                extreme_type = "极端高温"
                extreme_factor = 0.4
            elif min_temp < -10:
                extreme_type = "极端低温"
                extreme_factor = 0.5
            elif precipitation > 50:
                extreme_type = "暴雨"
                extreme_factor = 0.3
            elif wind_power > 6:
                extreme_type = "大风"
                extreme_factor = 0.6
            elif precipitation > 100:
                extreme_type = "大暴雨"
                extreme_factor = 0.2
            elif wind_power > 12:
                extreme_type = "台风"
                extreme_factor = 0.1
            
            prediction = prediction * extreme_factor
            change_reason.append(f"{extreme_type}影响，客流量减少 {int((1 - extreme_factor) * 100)}%")
        
        return int(prediction), change_reason
    
    def predict_future_traffic(self, attraction_name, weather_forecast, is_holiday=False):
        """预测未来客流量
        
        Args:
            attraction_name: 景点名称
            weather_forecast: 未来天气预报数据
            is_holiday: 是否为节假日
            
        Returns:
            list: 每日预测客流量
        """
        predictions = []
        
        for forecast in weather_forecast:
            try:
                # 提取必要的天气数据，添加默认值处理
                date = forecast.get('日期', forecast.get('date', ''))
                date_obj = pd.to_datetime(date)
                max_temp = forecast.get('最高气温', forecast.get('max_temp', 20))
                min_temp = forecast.get('最低气温', forecast.get('min_temp', 10))
                precipitation = forecast.get('降水量', forecast.get('precipitation', 0))
                wind_power = forecast.get('风力', forecast.get('wind', 2))
                weather = forecast.get('天气状况', forecast.get('weather', '晴'))
                
                # 计算平均气温
                avg_temp = (max_temp + min_temp) / 2
                
                # 计算星期几
                weekday = date_obj.dayofweek
                
                # 判断是否为周末
                is_weekend = 1 if weekday >= 5 else 0
                
                # 判断是否为节假日
                is_holiday_flag = 1 if self._is_holiday(date_obj) else 0
                
                # 判断是否为极端天气
                def is_extreme_weather(max_temp, min_temp, precipitation, wind_power):
                    # 极端高温 (>35°C)
                    if max_temp > 35:
                        return 1
                    # 极端低温 (<-10°C)
                    elif min_temp < -10:
                        return 1
                    # 暴雨 (>30mm)
                    elif precipitation > 30:
                        return 1
                    # 大风 (>6级)
                    elif wind_power > 6:
                        return 1
                    else:
                        return 0
                
                extreme_weather = is_extreme_weather(max_temp, min_temp, precipitation, wind_power)
                
                # 准备特征数据，确保使用与训练时相同的特征名
                forecast_df = pd.DataFrame({
                    '最高气温': [max_temp],
                    '最低气温': [min_temp],
                    '平均气温': [avg_temp],
                    '降水量': [precipitation],
                    '风力(白天)_数值': [wind_power],
                    '月份': [date_obj.month],
                    '星期': [weekday],
                    '是否周末': [is_weekend],
                    '是否节假日': [is_holiday_flag],
                    '极端天气': [extreme_weather]
                })
                
                # 预测客流量
                traffic, change_reason = self.predict_traffic(attraction_name, forecast_df, is_holiday_flag)
                
                predictions.append({
                    'date': date,
                    'traffic': traffic,
                    'weather': weather,
                    'change_reason': change_reason,
                    'is_holiday': is_holiday_flag,
                    'is_extreme_weather': extreme_weather
                })
            except Exception as e:
                # 添加错误处理，确保单个预测失败不会影响整个请求
                predictions.append({
                    'date': forecast.get('日期', forecast.get('date', '')),
                    'traffic': 0,
                    'weather': forecast.get('天气状况', forecast.get('weather', '未知')),
                    'error': str(e),
                    'change_reason': [],
                    'is_holiday': 0,
                    'is_extreme_weather': 0
                })
        
        return predictions
    
    def get_attraction_list(self):
        """获取所有景点列表
        
        Returns:
            list: 景点名称列表
        """
        return sorted(self.attractions_df['景点名称'].unique())
    
    def get_city_attractions(self, city):
        """获取城市的所有景点
        
        Args:
            city: 城市名称
            
        Returns:
            list: 景点名称列表
        """
        city_attractions = self.attractions_df[self.attractions_df['城市'] == city]
        return sorted(city_attractions['景点名称'].unique())
    
    def analyze_weather_traffic_correlation(self, attraction_name, weather_data=None):
        """分析历史天气与客流量的关联规律，提供运营建议
        
        Args:
            attraction_name: 景点名称
            weather_data: 可选，历史天气数据
            
        Returns:
            dict: 关联分析结果和运营建议
        """
        try:
            # 准备训练数据，这会生成包含天气和客流量的模拟数据
            X_train, X_test, y_train, y_test = self._prepare_training_data(attraction_name)
            
            # 合并训练和测试数据以便进行全面分析
            import pandas as pd
            X = pd.concat([X_train, X_test])
            y = pd.concat([y_train, y_test])
            
            # 创建包含所有特征和标签的完整数据集
            analysis_df = X.copy()
            analysis_df['客流量'] = y
            
            # 计算各个天气因素与客流量的相关性
            correlation = analysis_df.corr()['客流量'].drop('客流量')
            
            # 分析不同天气条件下的平均客流量
            weather_impact = {
                '不同温度范围的客流量': {
                    '低温 (<10°C)': analysis_df[analysis_df['平均气温'] < 10]['客流量'].mean(),
                    '中温 (10-25°C)': analysis_df[(analysis_df['平均气温'] >= 10) & (analysis_df['平均气温'] <= 25)]['客流量'].mean(),
                    '高温 (>25°C)': analysis_df[analysis_df['平均气温'] > 25]['客流量'].mean()
                },
                '降水对客流量的影响': {
                    '无降水': analysis_df[analysis_df['降水量'] == 0]['客流量'].mean(),
                    '少量降水 (<10mm)': analysis_df[(analysis_df['降水量'] > 0) & (analysis_df['降水量'] < 10)]['客流量'].mean(),
                    '中量降水 (10-30mm)': analysis_df[(analysis_df['降水量'] >= 10) & (analysis_df['降水量'] < 30)]['客流量'].mean(),
                    '大量降水 (≥30mm)': analysis_df[analysis_df['降水量'] >= 30]['客流量'].mean()
                },
                '风力对客流量的影响': {
                    '微风 (<3级)': analysis_df[analysis_df['风力(白天)_数值'] < 3]['客流量'].mean(),
                    '中风 (3-6级)': analysis_df[(analysis_df['风力(白天)_数值'] >= 3) & (analysis_df['风力(白天)_数值'] < 6)]['客流量'].mean(),
                    '大风 (≥6级)': analysis_df[analysis_df['风力(白天)_数值'] >= 6]['客流量'].mean()
                },
                '节假日影响': {
                    '工作日': analysis_df[analysis_df['是否节假日'] == 0]['客流量'].mean(),
                    '周末/节假日': analysis_df[analysis_df['是否节假日'] == 1]['客流量'].mean()
                },
                '极端天气影响': {
                    '正常天气': analysis_df[analysis_df['极端天气'] == 0]['客流量'].mean(),
                    '极端天气': analysis_df[analysis_df['极端天气'] == 1]['客流量'].mean()
                }
            }
            
            # 生成运营建议
            operation_suggestions = []
            
            # 温度相关建议
            temp_corr = correlation.get('平均气温', 0)
            if temp_corr > 0.3:
                operation_suggestions.append("高温天气客流量较高，建议增加高温天气下的服务人员和防暑设施")
            elif temp_corr < -0.3:
                operation_suggestions.append("低温天气客流量较低，建议推出冬季促销活动和室内娱乐项目")
            
            # 降水相关建议
            rain_corr = correlation.get('降水量', 0)
            if rain_corr < -0.3:
                operation_suggestions.append("雨天客流量明显减少，建议雨天推出线上促销或室内活动")
                operation_suggestions.append("加强景区内的避雨设施和排水系统")
            
            # 风力相关建议
            wind_corr = correlation.get('风力(白天)_数值', 0)
            if wind_corr < -0.2:
                operation_suggestions.append("大风天气客流量减少，建议大风天气注意户外设施安全，适当调整开放时间")
            
            # 节假日相关建议
            holiday_corr = correlation.get('是否节假日', 0)
            if holiday_corr > 0.5:
                operation_suggestions.append("节假日客流量显著增加，建议提前做好人员调配和物资准备")
                operation_suggestions.append("节假日期间可以推出特色活动和联合促销")
            
            # 极端天气相关建议
            extreme_corr = correlation.get('极端天气', 0)
            if extreme_corr < -0.4:
                operation_suggestions.append("极端天气对客流量影响大，建议建立极端天气应急预案")
                operation_suggestions.append("极端天气前通过多种渠道向游客发布预警信息")
            
            # 生成综合建议
            avg_weekday_traffic = weather_impact['节假日影响']['工作日']
            avg_holiday_traffic = weather_impact['节假日影响']['周末/节假日']
            if avg_holiday_traffic > avg_weekday_traffic * 1.5:
                operation_suggestions.append("周末和节假日客流量是工作日的1.5倍以上，建议重点优化节假日运营策略")
            
            # 生成季节性建议
            season_traffic = {
                '春季': analysis_df[(analysis_df['月份'] >= 3) & (analysis_df['月份'] <= 5)]['客流量'].mean(),
                '夏季': analysis_df[(analysis_df['月份'] >= 6) & (analysis_df['月份'] <= 8)]['客流量'].mean(),
                '秋季': analysis_df[(analysis_df['月份'] >= 9) & (analysis_df['月份'] <= 11)]['客流量'].mean(),
                '冬季': analysis_df[(analysis_df['月份'] == 12) | (analysis_df['月份'] <= 2)]['客流量'].mean()
            }
            
            peak_season = max(season_traffic, key=season_traffic.get)
            low_season = min(season_traffic, key=season_traffic.get)
            
            operation_suggestions.append(f"{peak_season}是旺季，建议提前做好资源调配和活动策划")
            operation_suggestions.append(f"{low_season}是淡季，建议推出促销活动和特色项目吸引游客")
            
            return {
                'success': True,
                'attraction_name': attraction_name,
                'correlation_analysis': {
                    'factors': correlation.to_dict(),
                    'weather_impact': weather_impact,
                    'seasonal_traffic': season_traffic
                },
                'operation_suggestions': operation_suggestions,
                'peak_season': peak_season,
                'low_season': low_season
            }
        except Exception as e:
            logger.error(f"分析天气-客流量关联规律失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_operation_analysis_report(self, attraction_name, time_range='year'):
        """获取运营分析报告
        
        Args:
            attraction_name: 景点名称
            time_range: 时间范围，可选值：'week', 'month', 'quarter', 'year'
            
        Returns:
            dict: 运营分析报告
        """
        try:
            # 获取天气-客流量关联分析
            correlation_result = self.analyze_weather_traffic_correlation(attraction_name)
            
            if not correlation_result['success']:
                return correlation_result
            
            # 生成报告
            report = {
                'attraction_name': attraction_name,
                'report_date': datetime.now().strftime('%Y-%m-%d'),
                'time_range': time_range,
                'correlation_analysis': correlation_result['correlation_analysis'],
                'operation_suggestions': correlation_result['operation_suggestions'],
                'key_insights': [
                    f"旺季：{correlation_result['peak_season']}",
                    f"淡季：{correlation_result['low_season']}",
                    f"节假日客流量影响：{'显著' if correlation_result['correlation_analysis']['factors'].get('是否节假日', 0) > 0.5 else '一般'}",
                    f"天气敏感度：{'高' if abs(correlation_result['correlation_analysis']['factors'].get('平均气温', 0)) > 0.3 else '中' if abs(correlation_result['correlation_analysis']['factors'].get('平均气温', 0)) > 0.1 else '低'}"
                ]
            }
            
            return {
                'success': True,
                'report': report
            }
        except Exception as e:
            logger.error(f"生成运营分析报告失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class TrafficPredictionServiceFactory:
    """客流量预测服务工厂类，用于创建不同类型的客流量预测服务"""
    
    @staticmethod
    def create_service(service_type="sklearn", data_dir=None):
        """创建客流量预测服务
        
        Args:
            service_type: 服务类型，支持 "sklearn" 或 "spark"
            data_dir: 数据目录路径
            
        Returns:
            TrafficPredictionService: 客流量预测服务实例
        """
        if service_type == "sklearn":
            return TrafficPredictionService(data_dir)
        elif service_type == "spark":
            # 未来可以实现Spark版本的客流量预测服务
            raise NotImplementedError("Spark版本的客流量预测服务尚未实现")
        else:
            raise ValueError(f"不支持的服务类型: {service_type}")
