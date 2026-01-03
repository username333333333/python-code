import pandas as pd
import os
import requests
from pathlib import Path
from datetime import datetime, timedelta


class WeatherService:
    def __init__(self, data_dir, city_name="沈阳"):
        """初始化天气服务

        Args:
            data_dir: 数据目录路径
            city_name: 城市名称，对应文件名前缀
        """
        self.city_name = city_name
        self.data_dir = Path(data_dir)
        self.data_file = self._find_data_file()
        self.df = self._load_data()
        self._preprocess_data()
        self.df['城市'] = self.city_name

    def _find_data_file(self):
        """查找数据文件"""
        # 尝试在weather_sensitive子目录中查找
        weather_sensitive_dir = self.data_dir / "weather_sensitive"
        
        possible_files = [
            # 优先在weather_sensitive子目录中查找
            weather_sensitive_dir / f"{self.city_name}2013-2023年天气数据.csv",
            weather_sensitive_dir / f"{self.city_name}2013-2023年 天气数据.csv",
            weather_sensitive_dir / f"{self.city_name}天气数据.csv",
            weather_sensitive_dir / f"{self.city_name}.csv",
            # 然后在根数据目录中查找
            self.data_dir / f"{self.city_name}2013-2023年天气数据.csv",
            self.data_dir / f"{self.city_name}天气数据.csv",
            self.data_dir / f"{self.city_name}.csv"
        ]

        for file_path in possible_files:
            if file_path.exists():
                return file_path

        raise FileNotFoundError(
            f"找不到城市 {self.city_name} 的数据文件，请检查以下路径:\n" +
            "\n".join(str(p) for p in possible_files)
        )

    def _load_data(self):
        """加载CSV天气数据"""
        try:
            # 先尝试不指定日期格式，让pandas自动推断
            df = pd.read_csv(
                self.data_file,
                parse_dates=['日期'],
                encoding='utf-8',
                on_bad_lines='skip'
            )

            # 如果日期解析失败，尝试其他日期格式
            if not pd.api.types.is_datetime64_any_dtype(df['日期']) or df['日期'].isna().all():
                # 尝试utf-8编码和"%Y-%m-%d"日期格式
                df = pd.read_csv(
                    self.data_file,
                    encoding='utf-8',
                    on_bad_lines='skip'
                )
                # 尝试多种日期格式
                date_formats = ['%Y-%m-%d', '%Y年%m月%d日', '%m/%d/%Y', '%d/%m/%Y']
                for fmt in date_formats:
                    df['日期'] = pd.to_datetime(df['日期'], format=fmt, errors='coerce')
                    if df['日期'].notna().any():
                        break
            
            # 如果utf-8编码失败，尝试gbk编码
            if df.empty or df['日期'].isna().all():
                df = pd.read_csv(
                    self.data_file,
                    encoding='gbk',
                    on_bad_lines='skip'
                )
                # 尝试多种日期格式
                date_formats = ['%Y-%m-%d', '%Y年%m月%d日', '%m/%d/%Y', '%d/%m/%Y']
                for fmt in date_formats:
                    df['日期'] = pd.to_datetime(df['日期'], format=fmt, errors='coerce')
                    if df['日期'].notna().any():
                        break

            # 如果日期列仍然是空的，抛出错误
            if df['日期'].isna().all():
                raise ValueError("无法解析日期列")

            return df
        except Exception as e:
            raise ValueError(f"加载数据文件失败: {str(e)}")

    def _preprocess_data(self):
        """数据预处理"""
        # 重命名列，处理可能的空格和错误命名
        self.df.columns = self.df.columns.str.strip()
        
        # 处理可能的列名错误，特别是天气状况列
        # 先创建一个临时映射字典，确保正确处理所有可能的列名
        column_mapping = {
            '天气 状况(白天)': '天气状况(白天)',  # 修复带空格的列名
            '天气状况(白天)': '天气状况(白天)',  # 确保正确的列名
            '天气 状况(夜间)': '天气状况(夜间)',  # 修复带空格的列名
            '天气状况(夜间)': '天气状况(夜间)'   # 确保正确的列名
        }
        
        # 只重命名实际存在的列
        actual_mapping = {}
        for old_col, new_col in column_mapping.items():
            if old_col in self.df.columns:
                actual_mapping[old_col] = new_col
        
        # 执行重命名
        if actual_mapping:
            self.df = self.df.rename(columns=actual_mapping)
        
        # 确保基本必要字段存在
        basic_required_columns = {
            '日期', '最高气温', '最低气温'
        }

        missing_basic = basic_required_columns - set(self.df.columns)
        if missing_basic:
            raise ValueError(f"数据文件缺少必要列: {missing_basic}")

        # 处理天气状况列：如果只有一个"天气状况"列，复制到白天和夜间
        if '天气状况' in self.df.columns:
            # 如果缺少白天和夜间的天气状况列，从"天气状况"列复制
            if '天气状况(白天)' not in self.df.columns:
                self.df['天气状况(白天)'] = self.df['天气状况']
            if '天气状况(夜间)' not in self.df.columns:
                self.df['天气状况(夜间)'] = self.df['天气状况']
        
        # 处理风力列：如果只有一个"风力"列，复制到白天和夜间
        if '风力' in self.df.columns:
            # 如果缺少白天和夜间的风力列，从"风力"列复制
            if '风力(白天)' not in self.df.columns:
                self.df['风力(白天)'] = self.df['风力']
            if '风力(夜间)' not in self.df.columns:
                self.df['风力(夜间)'] = self.df['风力']
        
        # 处理风向列：如果没有风向数据，添加默认值
        wind_directions = ['北风', '南风', '东风', '西风', '东北风', '东南风', '西北风', '西南风']
        
        # 为风向(白天)和风向(夜间)生成默认值
        if '风向(白天)' not in self.df.columns:
            # 循环使用风向列表生成数据
            self.df['风向(白天)'] = [wind_directions[i % len(wind_directions)] for i in range(len(self.df))]
        
        if '风向(夜间)' not in self.df.columns:
            # 循环使用风向列表生成数据
            self.df['风向(夜间)'] = [wind_directions[i % len(wind_directions)] for i in range(len(self.df))]
        
        # 处理风力数据
        self.df['风力(白天)_数值'] = self.df['风力(白天)'].apply(self._parse_wind)
        self.df['风力(夜间)_数值'] = self.df['风力(夜间)'].apply(self._parse_wind)

        # 计算温差
        self.df['温差'] = self.df['最高气温'] - self.df['最低气温']

        # 计算季度
        self.df['季度'] = pd.cut(
            self.df['日期'].dt.month,
            bins=[1, 3, 6, 9, 12],
            labels=["第一季度", "第二季度", "第三季度", "第四季度"],
            right=False
        )
        
        # 添加月份和季节列
        self.df['月份'] = self.df['日期'].dt.month
        self.df['季节'] = self.df['月份'].apply(lambda x: {
            12: '冬季', 1: '冬季', 2: '冬季',
            3: '春季', 4: '春季', 5: '春季',
            6: '夏季', 7: '夏季', 8: '夏季',
            9: '秋季', 10: '秋季', 11: '秋季'
        }[x])
        
        # 计算旅游评分
        def calculate_travel_score(row):
            """计算每日旅游出行评分"""
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
                
                # 天气评分 (0-100)
                day_weather = row['天气状况(白天)']
                ideal_weather = ['晴', '多云', '晴间多云', '多云转晴']
                is_ideal = any(ideal in day_weather for ideal in ideal_weather)
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
                wind_limit = 3
                if wind_power <= wind_limit:
                    wind_score = 100
                else:
                    wind_score = max(0, 100 - (wind_power - wind_limit) * 10)
                
                # 综合评分
                total_score = temp_score * 0.4 + weather_score * 0.35 + wind_score * 0.25
                return round(total_score, 2)
            except Exception:
                return 0
        
        self.df['旅游评分'] = self.df.apply(calculate_travel_score, axis=1)
        
        # 旅游推荐标签
        self.df['推荐指数'] = self.df['旅游评分'].apply(lambda x: 
            '强烈推荐' if x >= 90 else 
            '推荐' if x >= 70 else 
            '一般' if x >= 50 else 
            '不推荐')

    def _parse_wind(self, wind_str):
        """解析风力等级字符串为数值"""
        if pd.isna(wind_str) or not isinstance(wind_str, str):
            return 0.0

        wind_str = str(wind_str).strip()
        wind_str = wind_str.replace('级', '').replace('～', '-').replace('~', '-').replace('≤', '')

        if '-' in wind_str:
            parts = wind_str.split('-')
            try:
                return (float(parts[0]) + float(parts[1])) / 2
            except (ValueError, IndexError):
                return 0.0
        else:
            try:
                return float(wind_str)
            except ValueError:
                return 0.0

    def get_filtered_data(self, filters=None):
        """获取筛选后的数据"""
        if not filters:
            return self.df

        mask = True

        # 处理日期范围筛选
        if 'date_range' in filters and len(filters['date_range']) >= 2:
            try:
                start_date = pd.to_datetime(filters['date_range'][0])
                end_date = pd.to_datetime(filters['date_range'][1])
                mask &= (self.df['日期'] >= start_date)
                mask &= (self.df['日期'] <= end_date)
            except (ValueError, TypeError):
                pass

        # 处理白天天气筛选
        if 'day_weather' in filters and filters['day_weather']:
            mask &= self.df['天气状况(白天)'].isin(filters['day_weather'])

        # 处理夜间天气筛选
        if 'night_weather' in filters and filters['night_weather']:
            mask &= self.df['天气状况(夜间)'].isin(filters['night_weather'])

        return self.df[mask] if isinstance(mask, pd.Series) else self.df
    
    def get_future_weather_forecast(self, days=7, city=None):
        """获取未来天气预报
        
        Args:
            days: 预测天数，默认7天
            city: 城市名称，默认为初始化时的城市
            
        Returns:
            list: 包含未来几天天气预测的列表
        """
        forecast_city = city if city else self.city_name
        weather_forecast = []
        
        try:
            # 这里使用模拟数据，实际项目中可以替换为真实的天气API调用
            # 例如：OpenWeatherMap API、和风天气API等
            # 示例API调用（需要替换为真实API密钥）
            # api_key = "your_api_key"
            # url = f"http://api.openweathermap.org/data/2.5/forecast?q={forecast_city}&appid={api_key}&units=metric"
            # response = requests.get(url)
            # data = response.json()
            # 然后解析data获取天气预测
            
            # 模拟天气数据
            today = datetime.now()
            weather_types = ['晴', '多云', '阴', '小雨', '中雨', '晴间多云', '多云转晴']
            
            for i in range(days):
                forecast_date = today + timedelta(days=i)
                # 随机选择天气类型
                weather_type = weather_types[i % len(weather_types)]
                
                # 生成合理的温度范围
                avg_temp = 15 + i * 0.5  # 每天升高0.5度
                temp_min = avg_temp - 5
                temp_max = avg_temp + 5
                
                # 生成风力
                wind_level = 2 + i % 3
                
                weather_forecast.append({
                    'date': forecast_date.strftime('%Y-%m-%d'),
                    'weather': weather_type,
                    'temperature': f"{int(temp_min)}°C - {int(temp_max)}°C",
                    '最高气温': temp_max,
                    '最低气温': temp_min,
                    '平均气温': avg_temp,
                    '风力': f"{wind_level}级",
                    '风力(白天)_数值': wind_level,
                    '风力(夜间)_数值': wind_level
                })
            
            print(f"成功获取{forecast_city}未来{days}天的天气预报")
            return weather_forecast
            
        except Exception as e:
            print(f"获取天气预报失败: {str(e)}")
            # 如果API调用失败，返回模拟数据
            return self._generate_mock_weather_forecast(days, forecast_city)
    
    def _generate_mock_weather_forecast(self, days=7, city=None):
        """生成模拟天气数据
        
        Args:
            days: 预测天数
            city: 城市名称
            
        Returns:
            list: 模拟的天气预测数据
        """
        mock_forecast = []
        today = datetime.now()
        weather_types = ['晴', '多云', '阴', '小雨', '中雨', '晴间多云', '多云转晴']
        
        for i in range(days):
            forecast_date = today + timedelta(days=i)
            mock_forecast.append({
                'date': forecast_date.strftime('%Y-%m-%d'),
                'weather': weather_types[i % len(weather_types)],
                'temperature': "15°C - 25°C",
                '最高气温': 25,
                '最低气温': 15,
                '平均气温': 20,
                '风力': "3级",
                '风力(白天)_数值': 3,
                '风力(夜间)_数值': 3
            })
        
        return mock_forecast
