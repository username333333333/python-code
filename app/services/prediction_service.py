import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error
from datetime import datetime, timedelta
import joblib
import os
import hashlib
from pathlib import Path
from abc import ABC, abstractmethod


class WeatherPredictionInterface(ABC):
    """天气预测服务接口，定义核心功能，便于未来扩展到Spark实现
    
    该接口设计遵循开闭原则，允许新增不同的预测服务实现（如Sklearn、Spark）
    而无需修改调用方代码。所有实现类需确保返回格式一致，便于上层应用处理。
    """
    
    @abstractmethod
    def __init__(self, data_dir):
        """初始化预测服务
        
        Args:
            data_dir: 数据目录路径，用于模型存储和加载
        """
        pass
    
    @abstractmethod
    def train_all_models(self, weather_df):
        """为所有城市训练预测模型
        
        Args:
            weather_df: 包含历史天气数据的DataFrame
            要求列：城市, 日期, 最高气温, 最低气温, 平均气温, 风力(白天)_数值, 风力(夜间)_数值
        
        Returns:
            dict: 包含各城市各目标变量的训练结果，格式如下：
            {
                '城市1': {
                    '最高气温': {'model': 模型实例, 'mae': 平均绝对误差, 'rmse': 均方根误差},
                    '最低气温': {...}
                },
                '城市2': {...}
            }
        """
        pass
    
    @abstractmethod
    def predict_future(self, weather_df, city_name, days=7):
        """预测指定城市未来几天的天气
        
        Args:
            weather_df: 包含历史天气数据的DataFrame
            city_name: 要预测的城市名称
            days: 预测天数，默认7天
        
        Returns:
            DataFrame: 包含预测结果，要求列：
            日期, 最高气温, 最低气温, 平均气温, 风力(白天)_数值, 风力(夜间)_数值, 城市, 旅游评分, 推荐指数
        """
        pass
    
    @abstractmethod
    def predict_all_cities(self, weather_df, days=7):
        """预测所有城市未来几天的天气
        
        Args:
            weather_df: 包含历史天气数据的DataFrame
            days: 预测天数，默认7天
        
        Returns:
            dict: 以城市名为键，预测结果DataFrame为值的字典
        """
        pass
    
    @abstractmethod
    def get_model_performance(self, city_name, target_var):
        """获取指定城市指定目标变量的模型性能指标
        
        Args:
            city_name: 城市名称
            target_var: 目标变量，如'最高气温'、'最低气温'等
        
        Returns:
            dict: 包含模型性能指标的字典，格式：
            {'status': 'trained/not_trained', 'model': 模型实例(如果已训练)} 
        """
        pass


class WeatherPredictionService(WeatherPredictionInterface):
    """基于Scikit-learn的天气预测服务类"""
    
    def __init__(self, data_dir):
        """初始化预测服务"""
        self.data_dir = Path(data_dir)
        self.models = {}
        self.label_encoders = {}
        self.target_vars = ['最高气温', '最低气温', '平均气温', '风力(白天)_数值', '风力(夜间)_数值']
        self.model_dir = self.data_dir / 'models'
        self.model_dir.mkdir(exist_ok=True)
        
    def _generate_model_id(self, city_name, target_var):
        """生成模型的唯一标识符"""
        return f"{city_name}_{target_var}_model.joblib"
    
    def _load_model(self, city_name, target_var):
        """加载缓存的模型"""
        model_path = self.model_dir / self._generate_model_id(city_name, target_var)
        if model_path.exists():
            try:
                return joblib.load(model_path)
            except Exception as e:
                print(f"加载模型失败 {model_path}: {e}")
        return None
    
    def _save_model(self, model, city_name, target_var):
        """保存模型到缓存"""
        model_path = self.model_dir / self._generate_model_id(city_name, target_var)
        try:
            joblib.dump(model, model_path)
            return True
        except Exception as e:
            print(f"保存模型失败 {model_path}: {e}")
            return False
    
    def _prepare_features(self, df):
        """准备模型特征"""
        if df.empty:
            return df, {}
        
        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(df['日期']):
            df['日期'] = pd.to_datetime(df['日期'], format='%Y年%m月%d日', errors='coerce')
        
        # 创建时间特征
        df['月份'] = df['日期'].dt.month
        df['季节'] = df['月份'].apply(lambda x: {
            1: 0, 2: 0, 3: 1,
            4: 1, 5: 1, 6: 2,
            7: 2, 8: 2, 9: 3,
            10: 3, 11: 3, 12: 0
        }[x])
        df['年份'] = df['日期'].dt.year
        df['星期'] = df['日期'].dt.dayofweek
        df['日'] = df['日期'].dt.day
        
        # 编码分类特征
        categorical_cols = ['天气状况(白天)', '天气状况(夜间)', '风向(白天)', '风向(夜间)']
        encoders = {}
        
        for col in categorical_cols:
            if col in df.columns:
                le = LabelEncoder()
                df[col] = df[col].astype(str)
                df[col] = le.fit_transform(df[col])
                encoders[col] = le
                self.label_encoders[col] = le
        
        return df, encoders
    
    def train_model(self, df, city_name, target_var, test_size=0.2, random_state=42):
        """训练单个城市的天气预测模型"""
        if df.empty:
            return None, 0, 0
        
        # 尝试加载缓存的模型
        cached_model = self._load_model(city_name, target_var)
        if cached_model:
            self.models[(city_name, target_var)] = cached_model
            return cached_model, 0, 0
        
        # 准备特征
        df, encoders = self._prepare_features(df)
        
        # 选择特征列
        feature_cols = ['月份', '季节', '年份', '星期', '日']
        categorical_cols = ['天气状况(白天)', '天气状况(夜间)', '风向(白天)', '风向(夜间)']
        feature_cols += [col for col in categorical_cols if col in df.columns]
        
        if target_var not in df.columns:
            return None, 0, 0
        
        # 分离特征和目标变量
        X = df[feature_cols]
        y = df[target_var]
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
        
        # 训练模型
        model = RandomForestRegressor(n_estimators=100, random_state=random_state)
        model.fit(X_train, y_train)
        
        # 评估模型
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        # 保存模型到内存和磁盘
        self.models[(city_name, target_var)] = model
        self._save_model(model, city_name, target_var)
        
        return model, mae, rmse
    
    def train_all_models(self, weather_df):
        """为所有城市训练预测模型"""
        if weather_df.empty or '城市' not in weather_df.columns:
            return {}
        
        results = {}
        cities = weather_df['城市'].unique()
        
        for city in cities:
            city_df = weather_df[weather_df['城市'] == city].copy()
            city_results = {}
            
            for target_var in self.target_vars:
                if target_var in city_df.columns:
                    model, mae, rmse = self.train_model(city_df, city, target_var)
                    city_results[target_var] = {'model': model, 'mae': mae, 'rmse': rmse}
            
            results[city] = city_results
        
        return results
    
    def predict_future(self, weather_df, city_name, days=7):
        """预测未来几天的天气"""
        print(f"=== 开始预测天气: 城市={city_name}, 天数={days} ===")
        print(f"天气数据行数: {len(weather_df)}")
        print(f"城市列中的唯一值: {weather_df['城市'].unique()[:5]}...")
        
        if weather_df.empty:
            print("天气数据为空，返回空DataFrame")
            return pd.DataFrame()
        
        # 处理城市名称，确保与数据格式匹配
        # 数据中的城市名称可能带有"市"后缀，所以我们需要尝试两种格式
        city_df = weather_df[weather_df['城市'] == city_name].copy()
        print(f"使用城市名称'{city_name}'查找数据，找到{len(city_df)}行")
        
        has_city_suffix = city_name.endswith('市')
        
        if city_df.empty and not has_city_suffix:
            # 如果没有找到，尝试添加"市"后缀
            city_df = weather_df[weather_df['城市'] == city_name + '市'].copy()
            print(f"使用城市名称'{city_name}市'查找数据，找到{len(city_df)}行")
        
        if city_df.empty:
            print(f"没有找到城市'{city_name}'的数据，返回空DataFrame")
            return pd.DataFrame()
        
        # 从明天开始预测，而不是从历史数据的最后日期
        tomorrow = datetime.now().date() + timedelta(days=1)
        print(f"预测起始日期: {tomorrow}")
        
        # 生成未来日期
        future_dates = [tomorrow + timedelta(days=i) for i in range(days)]
        print(f"生成的未来日期: {future_dates}")
        
        # 为未来日期创建特征
        future_features = []
        for date in future_dates:
            feature = {
                '日期': date,
                '月份': date.month,
                '季节': {
                    1: 0, 2: 0, 3: 1,
                    4: 1, 5: 1, 6: 2,
                    7: 2, 8: 2, 9: 3,
                    10: 3, 11: 3, 12: 0
                }[date.month],
                '年份': date.year,
                '星期': date.weekday(),
                '日': date.day
            }
            future_features.append(feature)
        
        future_df = pd.DataFrame(future_features)
        print(f"未来特征数据行数: {len(future_df)}")
        
        # 加载城市的原始数据，用于获取分类特征的众数（原始值）
        original_city_df = weather_df[weather_df['城市'] == city_df['城市'].iloc[0]].copy()
        
        # 对于分类特征，使用历史数据的原始众数填充
        categorical_cols = ['天气状况(白天)', '天气状况(夜间)', '风向(白天)', '风向(夜间)']
        for col in categorical_cols:
            if col in original_city_df.columns:
                # 使用原始数据的众数（未编码的原始值）
                mode_val = original_city_df[col].mode()[0]
                future_df[col] = mode_val
                print(f"填充分类特征 '{col}' 使用原始众数值: {mode_val}")
        
        # 加载所有目标变量的模型，如果尚未加载
        for target_var in self.target_vars:
            # 尝试使用原始城市名称查找或加载模型
            model_city_name = city_name
            model_path = self.model_dir / self._generate_model_id(model_city_name, target_var)
            
            if not model_path.exists() and not has_city_suffix:
                # 如果没有找到，尝试使用带有"市"后缀的城市名称
                model_city_name = city_name + '市'
                model_path = self.model_dir / self._generate_model_id(model_city_name, target_var)
            
            model_key = (model_city_name, target_var)
            if model_key not in self.models:
                # 尝试从文件加载模型
                model = self._load_model(model_city_name, target_var)
                if model:
                    self.models[model_key] = model
                    print(f"从文件加载模型: {model_key}")
            else:
                print(f"模型已在内存中: {model_key}")
        
        # 准备特征：只处理数值特征，分类特征使用原始数据的编码器
        future_df_with_features = future_df.copy()
        
        # 手动添加时间特征（已经在前面创建）
        
        # 编码分类特征，使用历史数据的编码器
        # 首先准备历史数据的编码器
        city_df_with_encoders, encoders = self._prepare_features(city_df.copy())
        
        # 对未来数据的分类特征进行编码，使用与历史数据相同的编码器
        for col in categorical_cols:
            if col in future_df_with_features.columns and col in encoders:
                le = encoders[col]
                # 处理未知类别：使用众数或默认值
                future_df_with_features[col] = future_df_with_features[col].apply(lambda x: x if x in le.classes_ else city_df[col].mode()[0])
                # 使用历史编码器进行转换
                future_df_with_features[col] = le.transform(future_df_with_features[col].astype(str))
                print(f"使用历史编码器编码特征 '{col}'")
        
        print(f"编码后的未来特征数据列: {list(future_df_with_features.columns)}")
        
        # 打印当前模型列表
        print(f"当前模型列表: {list(self.models.keys())[:10]}...")
        
        # 预测每个目标变量
        for target_var in self.target_vars:
            # 确定使用的模型城市名称
            model_city_name = city_name
            if (model_city_name, target_var) not in self.models and not has_city_suffix:
                model_city_name = city_name + '市'
            
            model_key = (model_city_name, target_var)
            print(f"尝试模型键: {model_key}")
            
            if model_key in self.models:
                print(f"找到模型: {model_key}")
                model = self.models[model_key]
                # 选择特征列
                feature_cols = ['月份', '季节', '年份', '星期', '日']
                feature_cols += [col for col in categorical_cols if col in future_df_with_features.columns]
                print(f"使用特征列: {feature_cols}")
                
                X_future = future_df_with_features[feature_cols]
                print(f"特征数据形状: {X_future.shape}")
                future_df[target_var] = model.predict(X_future)
                print(f"预测完成: {target_var}")
            else:
                print(f"未找到模型: {model_key}")
                # 如果没有找到模型，尝试训练模型
                print(f"尝试训练模型: {model_key}")
                self.train_model(city_df, model_city_name, target_var)
                if model_key in self.models:
                    model = self.models[model_key]
                    feature_cols = ['月份', '季节', '年份', '星期', '日']
                    feature_cols += [col for col in categorical_cols if col in future_df_with_features.columns]
                    X_future = future_df_with_features[feature_cols]
                    future_df[target_var] = model.predict(X_future)
                    print(f"训练并预测完成: {target_var}")
                else:
                    # 如果仍然没有模型，设置默认值
                    future_df[target_var] = 15.0  # 默认温度
                    print(f"使用默认值: {target_var} = 15.0")
        
        print(f"预测结果列: {list(future_df.columns)}")
        print(f"预测结果行数: {len(future_df)}")
        print("=== 天气预测完成 ===")
        
        # 计算旅游评分
        if '最高气温' in future_df.columns and '最低气温' in future_df.columns:
            future_df['温差'] = future_df['最高气温'] - future_df['最低气温']
            future_df['城市'] = city_name
            
            # 简化的旅游评分计算，保留整数
            future_df['旅游评分'] = future_df.apply(lambda row: self._calculate_simple_travel_score(row), axis=1)
            future_df['旅游评分'] = future_df['旅游评分'].round().astype(int)
            future_df['推荐指数'] = future_df['旅游评分'].apply(lambda x: 
                '强烈推荐' if x >= 90 else 
                '推荐' if x >= 70 else 
                '一般' if x >= 50 else 
                '不推荐')
        
        return future_df
    
    def _calculate_simple_travel_score(self, row):
        """改进的旅游评分计算，根据季节调整评分标准"""
        try:
            # 获取月份，根据季节调整评分标准
            month = row['日期'].month
            is_winter = month in [12, 1, 2]  # 冬季：12月、1月、2月
            
            # 温度评分 (0-100) - 根据季节调整理想温度范围
            avg_temp = (row['最高气温'] + row['最低气温']) / 2
            if is_winter:
                # 冬季理想温度范围调整为-5到10°C
                ideal_min, ideal_max = -5, 10
                # 冬季温度评分更宽松
                if avg_temp < ideal_min:
                    temp_score = max(0, 80 - (ideal_min - avg_temp) * 3)  # 降低冬季低温的惩罚
                elif avg_temp > ideal_max:
                    temp_score = max(0, 100 - (avg_temp - ideal_max) * 5)
                else:
                    temp_score = 100
            else:
                # 其他季节保持原标准
                ideal_min, ideal_max = 15, 30
                if avg_temp < ideal_min:
                    temp_score = max(0, 100 - (ideal_min - avg_temp) * 5)
                elif avg_temp > ideal_max:
                    temp_score = max(0, 100 - (avg_temp - ideal_max) * 5)
                else:
                    temp_score = 100
            
            # 风力评分 (0-100) - 降低冬季风力的影响
            wind_power = (row['风力(白天)_数值'] + row['风力(夜间)_数值']) / 2
            wind_limit = 3
            if is_winter:
                # 冬季风力评分更宽松
                if wind_power <= wind_limit:
                    wind_score = 100
                elif wind_power <= 5:
                    wind_score = max(0, 100 - (wind_power - wind_limit) * 5)  # 降低风力惩罚
                else:
                    wind_score = max(0, 80 - (wind_power - 5) * 10)  # 强风惩罚
            else:
                # 其他季节保持原标准
                if wind_power <= wind_limit:
                    wind_score = 100
                else:
                    wind_score = max(0, 100 - (wind_power - wind_limit) * 10)
            
            # 温差评分 (0-100) - 温差适中更适合旅游
            temp_diff = row['温差']
            if is_winter:
                # 冬季温差范围调整
                ideal_diff_min, ideal_diff_max = 3, 18
                if temp_diff >= ideal_diff_min and temp_diff <= ideal_diff_max:
                    diff_score = 100
                elif temp_diff < ideal_diff_min:
                    diff_score = 80 + temp_diff * 3  # 冬季温差小更常见，降低惩罚
                else:
                    diff_score = 100 - (temp_diff - ideal_diff_max) * 2  # 降低温差大的惩罚
            else:
                # 其他季节保持原标准
                ideal_diff_min, ideal_diff_max = 5, 15
                if temp_diff >= ideal_diff_min and temp_diff <= ideal_diff_max:
                    diff_score = 100
                elif temp_diff < ideal_diff_min:
                    diff_score = 70 + temp_diff * 6
                else:
                    diff_score = 100 - (temp_diff - ideal_diff_max) * 3
            diff_score = max(0, min(100, diff_score))
            
            # 季节奖励 - 为冬季增加额外奖励，避免评分过低
            season_bonus = 0
            if is_winter:
                season_bonus = 10  # 冬季额外加10分
            
            # 日期随机性 (0-5分) - 增加每天评分的差异
            import random
            date_str = str(row['日期'])
            random.seed(date_str)  # 使用日期作为种子，确保同一天的评分一致但不同天不同
            random_score = random.uniform(0, 5)
            
            # 综合评分，调整权重
            total_score = temp_score * 0.45 + wind_score * 0.25 + diff_score * 0.15 + season_bonus + random_score
            total_score = max(0, min(100, total_score))  # 确保评分在0-100之间
            return round(total_score, 2)
        except Exception as e:
            print(f"计算旅游评分时出错: {e}")
            return 0
    
    def predict_all_cities(self, weather_df, days=7):
        """预测所有城市的未来天气"""
        if weather_df.empty or '城市' not in weather_df.columns:
            return {}
        
        predictions = {}
        cities = weather_df['城市'].unique()
        
        for city in cities:
            city_prediction = self.predict_future(weather_df, city, days)
            if not city_prediction.empty:
                predictions[city] = city_prediction
        
        return predictions
    
    def get_model_performance(self, city_name, target_var):
        """获取模型性能指标"""
        model_key = (city_name, target_var)
        if model_key in self.models:
            return {'status': 'trained', 'model': self.models[model_key]}
        return {'status': 'not_trained'}



class SparkWeatherPredictionService(WeatherPredictionInterface):
    """基于Spark的天气预测服务实现"""
    
    def __init__(self, data_dir):
        """初始化Spark预测服务"""
        from pyspark.sql import SparkSession
        
        self.data_dir = Path(data_dir)
        self.target_vars = ['最高气温', '最低气温', '平均气温', '风力(白天)_数值', '风力(夜间)_数值']
        self.models = {}
        
        # 初始化Spark会话
        self.spark = SparkSession.builder \
            .appName("WeatherPrediction") \
            .config("spark.sql.catalogImplementation", "hive") \
            .getOrCreate()
        
        print("Spark天气预测服务初始化完成")
    
    def train_all_models(self, weather_df):
        """使用Spark为所有城市训练预测模型"""
        from pyspark.sql import functions as F
        from pyspark.ml.feature import VectorAssembler, StringIndexer, OneHotEncoder
        from pyspark.ml.regression import RandomForestRegressor
        from pyspark.ml import Pipeline
        from pyspark.ml.evaluation import RegressionEvaluator
        
        if weather_df.empty or '城市' not in weather_df.columns:
            return {}
        
        # 将Pandas DataFrame转换为Spark DataFrame
        spark_df = self.spark.createDataFrame(weather_df)
        
        # 确保必要的特征列存在
        if '月份' not in spark_df.columns and '日期' in spark_df.columns:
            spark_df = spark_df.withColumn('月份', F.month('日期'))
        if '季节' not in spark_df.columns and '月份' in spark_df.columns:
            spark_df = spark_df.withColumn('季节', F.when((F.col('月份') >= 3) & (F.col('月份') <= 5), 1) \
                                           .when((F.col('月份') >= 6) & (F.col('月份') <= 8), 2) \
                                           .when((F.col('月份') >= 9) & (F.col('月份') <= 11), 3) \
                                           .otherwise(0))
        if '年份' not in spark_df.columns and '日期' in spark_df.columns:
            spark_df = spark_df.withColumn('年份', F.year('日期'))
        if '星期' not in spark_df.columns and '日期' in spark_df.columns:
            spark_df = spark_df.withColumn('星期', F.dayofweek('日期'))
        if '日' not in spark_df.columns and '日期' in spark_df.columns:
            spark_df = spark_df.withColumn('日', F.dayofmonth('日期'))
        
        results = {}
        cities = spark_df.select('城市').distinct().rdd.flatMap(lambda x: x).collect()
        
        for city in cities:
            city_df = spark_df.filter(spark_df.城市 == city)
            city_results = {}
            
            for target_var in self.target_vars:
                if target_var not in city_df.columns:
                    continue
                
                # 简单的特征工程
                feature_cols = ['月份', '季节', '年份', '星期', '日']
                
                # 训练模型
                rf = RandomForestRegressor(featuresCol="features", labelCol=target_var, numTrees=100)
                assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
                pipeline = Pipeline(stages=[assembler, rf])
                
                # 训练模型
                model = pipeline.fit(city_df)
                
                # 评估模型
                predictions = model.transform(city_df)
                evaluator = RegressionEvaluator(labelCol=target_var, predictionCol="prediction")
                mae = evaluator.evaluate(predictions, {evaluator.metricName: "mae"})
                rmse = evaluator.evaluate(predictions, {evaluator.metricName: "rmse"})
                
                # 保存模型
                model_path = str(self.data_dir / f"models/{city}_{target_var}_spark_model")
                model.save(model_path)
                
                city_results[target_var] = {'model': model, 'mae': mae, 'rmse': rmse}
            
            results[city] = city_results
        
        return results
    
    def predict_future(self, weather_df, city_name, days=7):
        """使用Spark预测指定城市未来几天的天气"""
        from pyspark.sql import functions as F
        from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType, DateType
        import pandas as pd
        from datetime import datetime, timedelta
        
        # 获取最近的日期
        if not weather_df.empty and '日期' in weather_df.columns:
            latest_date = pd.to_datetime(weather_df['日期']).max()
        else:
            latest_date = datetime.now()
        
        # 生成未来日期
        future_dates = [latest_date + timedelta(days=i) for i in range(1, days+1)]
        
        # 创建未来日期的DataFrame
        future_data = []
        for date in future_dates:
            future_data.append({
                '日期': date,
                '月份': date.month,
                '季节': {1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3, 12: 0}[date.month],
                '年份': date.year,
                '星期': date.weekday(),
                '日': date.day
            })
        
        future_df = pd.DataFrame(future_data)
        
        # 将Pandas DataFrame转换为Spark DataFrame
        spark_future_df = self.spark.createDataFrame(future_df)
        
        # 预测每个目标变量
        for target_var in self.target_vars:
            # 加载模型
            model_path = str(self.data_dir / f"models/{city_name}_{target_var}_spark_model")
            try:
                from pyspark.ml import PipelineModel
                model = PipelineModel.load(model_path)
                
                # 进行预测
                predictions = model.transform(spark_future_df)
                
                # 将预测结果转换回Pandas DataFrame
                predictions_pd = predictions.toPandas()
                
                # 将预测结果添加到未来数据中
                future_df[target_var] = predictions_pd['prediction']
            except Exception as e:
                print(f"加载或使用Spark模型失败: {e}")
                # 如果模型加载失败，使用默认值
                future_df[target_var] = 0
        
        # 计算旅游评分
        if '最高气温' in future_df.columns and '最低气温' in future_df.columns:
            future_df['温差'] = future_df['最高气温'] - future_df['最低气温']
            future_df['城市'] = city_name
            
            # 简化的旅游评分计算，保留整数
            future_df['旅游评分'] = future_df.apply(lambda row: self._calculate_simple_travel_score(row), axis=1)
            future_df['旅游评分'] = future_df['旅游评分'].round().astype(int)
            future_df['推荐指数'] = future_df['旅游评分'].apply(lambda x: 
                '强烈推荐' if x >= 90 else 
                '推荐' if x >= 70 else 
                '一般' if x >= 50 else 
                '不推荐')
        
        return future_df
    
    def _calculate_simple_travel_score(self, row):
        """简化的旅游评分计算"""
        try:
            # 温度评分 (0-100)
            avg_temp = (row['最高气温'] + row['最低气温']) / 2
            ideal_min, ideal_max = 15, 30
            if avg_temp < ideal_min:
                temp_score = max(0, 100 - (ideal_min - avg_temp) * 5)
            elif avg_temp > ideal_max:
                temp_score = max(0, 100 - (avg_temp - ideal_max) * 5)
            else:
                temp_score = 100
            
            # 风力评分 (0-100)
            wind_power = 3.0  # 默认值，Spark实现中可以根据实际数据计算
            if '风力(白天)_数值' in row and '风力(夜间)_数值' in row:
                wind_power = (row['风力(白天)_数值'] + row['风力(夜间)_数值']) / 2
            wind_limit = 3
            if wind_power <= wind_limit:
                wind_score = 100
            else:
                wind_score = max(0, 100 - (wind_power - wind_limit) * 10)
            
            # 综合评分
            total_score = temp_score * 0.7 + wind_score * 0.3
            return round(total_score, 2)
        except Exception:
            return 0
    
    def predict_all_cities(self, weather_df, days=7):
        """使用Spark预测所有城市的未来天气"""
        if weather_df.empty or '城市' not in weather_df.columns:
            return {}
        
        predictions = {}
        cities = weather_df['城市'].unique()
        
        for city in cities:
            city_prediction = self.predict_future(weather_df, city, days)
            if not city_prediction.empty:
                predictions[city] = city_prediction
        
        return predictions
    
    def get_model_performance(self, city_name, target_var):
        """获取Spark模型的性能指标"""
        # 简单实现，实际应该从模型训练结果中获取
        return {'status': 'trained'}


class WeatherPredictionServiceFactory:
    """天气预测服务工厂，用于创建不同类型的预测服务"""
    
    @staticmethod
    def create_service(service_type=None, data_dir="./data"):
        """创建天气预测服务实例
        
        Args:
            service_type: 服务类型，"sklearn"或"spark"，None时从配置文件获取
            data_dir: 数据目录
            
        Returns:
            WeatherPredictionInterface: 预测服务实例
        """
        from app.config import Config
        import platform
        
        # 如果没有指定服务类型，从配置文件获取
        if service_type is None:
            service_type = Config.PREDICTION_SERVICE_TYPE
            print(f"从配置文件获取预测服务类型: {service_type}")
        
        # 检查操作系统
        is_windows = platform.system() == "Windows"
        
        if service_type == "spark":
            if is_windows:
                # 在Windows系统上，PySpark可能会遇到兼容性问题，回退到使用Scikit-learn
                print("Windows系统上Spark可能遇到兼容性问题，回退使用Scikit-learn实现")
                return WeatherPredictionService(data_dir)
            else:
                try:
                    return SparkWeatherPredictionService(data_dir)
                except Exception as e:
                    # 如果Spark初始化失败，回退到使用Scikit-learn
                    print(f"Spark初始化失败: {e}，回退使用Scikit-learn实现")
                    return WeatherPredictionService(data_dir)
        elif service_type == "sklearn":
            return WeatherPredictionService(data_dir)
        else:
            raise ValueError(f"不支持的预测服务类型: {service_type}")
        
    def _generate_model_id(self, city_name, target_var):
        """生成模型的唯一标识符"""
        return f"{city_name}_{target_var}_model.joblib"
    
    def _load_model(self, city_name, target_var):
        """加载缓存的模型"""
        model_path = self.model_dir / self._generate_model_id(city_name, target_var)
        if model_path.exists():
            try:
                return joblib.load(model_path)
            except Exception as e:
                print(f"加载模型失败 {model_path}: {e}")
        return None
    
    def _save_model(self, model, city_name, target_var):
        """保存模型到缓存"""
        model_path = self.model_dir / self._generate_model_id(city_name, target_var)
        try:
            joblib.dump(model, model_path)
            return True
        except Exception as e:
            print(f"保存模型失败 {model_path}: {e}")
            return False
    
    def _prepare_features(self, df):
        """准备模型特征"""
        if df.empty:
            return df, {}
        
        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(df['日期']):
            df['日期'] = pd.to_datetime(df['日期'], format='%Y年%m月%d日', errors='coerce')
        
        # 创建时间特征
        df['月份'] = df['日期'].dt.month
        df['季节'] = df['月份'].apply(lambda x: {
            1: 0, 2: 0, 3: 1,
            4: 1, 5: 1, 6: 2,
            7: 2, 8: 2, 9: 3,
            10: 3, 11: 3, 12: 0
        }[x])
        df['年份'] = df['日期'].dt.year
        df['星期'] = df['日期'].dt.dayofweek
        df['日'] = df['日期'].dt.day
        
        # 编码分类特征
        categorical_cols = ['天气状况(白天)', '天气状况(夜间)', '风向(白天)', '风向(夜间)']
        encoders = {}
        
        for col in categorical_cols:
            if col in df.columns:
                le = LabelEncoder()
                # 处理未知类别
                df[col] = df[col].astype(str)
                df[col] = le.fit_transform(df[col])
                encoders[col] = le
                self.label_encoders[col] = le
        
        return df, encoders
    
    def train_model(self, df, city_name, target_var, test_size=0.2, random_state=42):
        """训练单个城市的天气预测模型"""
        if df.empty:
            return None, 0, 0
        
        # 尝试加载缓存的模型
        cached_model = self._load_model(city_name, target_var)
        if cached_model:
            # 模型已存在，直接返回
            self.models[(city_name, target_var)] = cached_model
            # 由于是缓存模型，返回默认的性能指标
            return cached_model, 0, 0
        
        # 准备特征
        df, encoders = self._prepare_features(df)
        
        # 选择特征列
        feature_cols = ['月份', '季节', '年份', '星期', '日']
        categorical_cols = ['天气状况(白天)', '天气状况(夜间)', '风向(白天)', '风向(夜间)']
        feature_cols += [col for col in categorical_cols if col in df.columns]
        
        # 确保目标变量存在
        if target_var not in df.columns:
            return None, 0, 0
        
        # 分离特征和目标变量
        X = df[feature_cols]
        y = df[target_var]
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
        
        # 训练模型
        model = RandomForestRegressor(n_estimators=100, random_state=random_state)
        model.fit(X_train, y_train)
        
        # 评估模型
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        # 保存模型到内存和磁盘
        self.models[(city_name, target_var)] = model
        self._save_model(model, city_name, target_var)
        
        return model, mae, rmse
    
    def train_all_models(self, weather_df):
        """为所有城市训练预测模型"""
        if weather_df.empty or '城市' not in weather_df.columns:
            return {}
        
        results = {}
        cities = weather_df['城市'].unique()
        
        for city in cities:
            city_df = weather_df[weather_df['城市'] == city].copy()
            city_results = {}
            
            for target_var in self.target_vars:
                if target_var in city_df.columns:
                    model, mae, rmse = self.train_model(city_df, city, target_var)
                    city_results[target_var] = {'model': model, 'mae': mae, 'rmse': rmse}
            
            results[city] = city_results
        
        return results
    
    def predict_future(self, weather_df, city_name, days=7):
        """预测未来几天的天气"""
        if weather_df.empty:
            return pd.DataFrame()
        
        # 获取城市历史数据
        city_df = weather_df[weather_df['城市'] == city_name].copy()
        if city_df.empty:
            return pd.DataFrame()
        
        # 准备历史数据特征
        city_df, _ = self._prepare_features(city_df)
        
        # 获取最近的日期作为预测起点
        last_date = city_df['日期'].max()
        
        # 生成未来日期
        future_dates = [last_date + timedelta(days=i+1) for i in range(days)]
        
        # 为未来日期创建特征
        future_features = []
        for date in future_dates:
            feature = {
                '日期': date,
                '月份': date.month,
                '季节': {
                    1: 0, 2: 0, 3: 1,
                    4: 1, 5: 1, 6: 2,
                    7: 2, 8: 2, 9: 3,
                    10: 3, 11: 3, 12: 0
                }[date.month],
                '年份': date.year,
                '星期': date.weekday(),
                '日': date.day
            }
            future_features.append(feature)
        
        future_df = pd.DataFrame(future_features)
        
        # 对于分类特征，使用历史数据的众数填充
        categorical_cols = ['天气状况(白天)', '天气状况(夜间)', '风向(白天)', '风向(夜间)']
        for col in categorical_cols:
            if col in city_df.columns:
                # 使用历史数据的众数
                mode_val = city_df[col].mode()[0]
                future_df[col] = mode_val
        
        # 预测每个目标变量
        predictions = {}
        for target_var in self.target_vars:
            model_key = (city_name, target_var)
            if model_key in self.models:
                model = self.models[model_key]
                # 选择特征列
                feature_cols = ['月份', '季节', '年份', '星期', '日']
                feature_cols += [col for col in categorical_cols if col in future_df.columns]
                
                X_future = future_df[feature_cols]
                future_df[target_var] = model.predict(X_future)
        
        # 计算旅游评分
        if '最高气温' in future_df.columns and '最低气温' in future_df.columns:
            future_df['温差'] = future_df['最高气温'] - future_df['最低气温']
            future_df['城市'] = city_name
            
            # 简化的旅游评分计算，保留整数
            future_df['旅游评分'] = future_df.apply(lambda row: self._calculate_simple_travel_score(row), axis=1)
            future_df['旅游评分'] = future_df['旅游评分'].round().astype(int)
            future_df['推荐指数'] = future_df['旅游评分'].apply(lambda x: 
                '强烈推荐' if x >= 90 else 
                '推荐' if x >= 70 else 
                '一般' if x >= 50 else 
                '不推荐')
        
        return future_df
    
    def _calculate_simple_travel_score(self, row):
        """简化的旅游评分计算"""
        try:
            # 温度评分 (0-100)
            avg_temp = (row['最高气温'] + row['最低气温']) / 2
            ideal_min, ideal_max = 15, 30
            if avg_temp < ideal_min:
                temp_score = max(0, 100 - (ideal_min - avg_temp) * 5)
            elif avg_temp > ideal_max:
                temp_score = max(0, 100 - (avg_temp - ideal_max) * 5)
            else:
                temp_score = 100
            
            # 风力评分 (0-100)
            wind_power = (row['风力(白天)_数值'] + row['风力(夜间)_数值']) / 2
            wind_limit = 3
            if wind_power <= wind_limit:
                wind_score = 100
            else:
                wind_score = max(0, 100 - (wind_power - wind_limit) * 10)
            
            # 综合评分 (简化版，暂不考虑天气状况)
            total_score = temp_score * 0.7 + wind_score * 0.3
            return round(total_score, 2)
        except Exception:
            return 0
    
    def predict_all_cities(self, weather_df, days=7):
        """预测所有城市的未来天气"""
        if weather_df.empty or '城市' not in weather_df.columns:
            return {}
        
        predictions = {}
        cities = weather_df['城市'].unique()
        
        for city in cities:
            city_prediction = self.predict_future(weather_df, city, days)
            if not city_prediction.empty:
                predictions[city] = city_prediction
        
        return predictions
    
    def get_model_performance(self, city_name, target_var):
        """获取模型性能指标"""
        model_key = (city_name, target_var)
        if model_key in self.models:
            # 这里可以返回更详细的性能指标
            return {'status': 'trained', 'model': self.models[model_key]}
        return {'status': 'not_trained'}
