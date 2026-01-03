from app.utils.data_loader import load_all_city_data, load_attractions_data
import pandas as pd
from datetime import datetime, timedelta

class OperationAnalysisService:
    """景区运营决策辅助服务
    
    分析历史天气与客流量的关联规律，为景区提供运营建议
    """
    
    def __init__(self, data_dir):
        """初始化服务
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.attractions_df = load_attractions_data(data_dir)
        
    def _load_historical_data(self):
        """加载历史数据
        
        Returns:
            pd.DataFrame: 历史数据
        """
        # 加载所有天气数据
        weather_df = load_all_city_data()
        
        # 为每个城市生成模拟的客流量数据
        all_data = []
        
        for city in weather_df['城市'].unique():
            city_weather = weather_df[weather_df['城市'] == city].copy()
            
            # 生成模拟客流量数据
            base_traffic = 1000
            
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
            
            # 计算最终客流量
            import numpy as np
            # 使用当前时间作为随机种子，确保每次运行结果不同
            np.random.seed(int(datetime.now().timestamp()))
            city_weather['客流量'] = base_traffic * city_weather['天气系数'] * city_weather['季节系数']
            city_weather['客流量'] = city_weather['客流量'] * (0.8 + np.random.rand(len(city_weather)) * 0.4)
            city_weather['客流量'] = city_weather['客流量'].astype(int)
            
            # 计算平均气温
            city_weather['平均气温'] = (city_weather['最高气温'] + city_weather['最低气温']) / 2
            
            all_data.append(city_weather)
        
        return pd.concat(all_data, ignore_index=True)
    
    def _analyze_historical_patterns(self, attraction_name):
        """分析历史天气与客流量的关联模式
        
        Args:
            attraction_name: 景点名称
            
        Returns:
            dict: 历史模式分析结果
        """
        # 获取景点所在城市
        attraction = self.attractions_df[self.attractions_df['景点名称'] == attraction_name]
        if attraction.empty:
            raise ValueError(f"景点 {attraction_name} 不存在")
        
        city = attraction.iloc[0]['城市']
        
        # 加载历史数据
        historical_data = self._load_historical_data()
        
        # 筛选该城市的数据
        city_data = historical_data[historical_data['城市'] == city]
        
        # 分析不同天气条件下的客流量模式
        weather_patterns = {}
        
        # 按天气状况分组分析
        for weather, group in city_data.groupby('天气状况(白天)'):
            if len(group) > 10:  # 至少需要10个样本
                weather_patterns[weather] = {
                    'avg_traffic': int(group['客流量'].mean()),
                    'max_traffic': group['客流量'].max(),
                    'min_traffic': group['客流量'].min(),
                    'std_traffic': group['客流量'].std(),
                    'count': len(group)
                }
        
        # 分析不同季节的客流量模式
        season_patterns = {}
        for season, group in city_data.groupby('季节'):
            season_patterns[season] = {
                'avg_traffic': int(group['客流量'].mean()),
                'max_traffic': group['客流量'].max(),
                'min_traffic': group['客流量'].min(),
                'count': len(group)
            }
        
        # 分析不同温度范围的客流量模式
        temp_bins = [-20, 0, 10, 20, 30, 40]
        temp_labels = ['极寒', '寒冷', '凉爽', '温暖', '炎热']
        city_data['温度范围'] = pd.cut(city_data['平均气温'], bins=temp_bins, labels=temp_labels)
        
        temp_patterns = {}
        for temp_range, group in city_data.groupby('温度范围'):
            if len(group) > 10:
                temp_patterns[str(temp_range)] = {
                    'avg_traffic': int(group['客流量'].mean()),
                    'count': len(group)
                }
        
        return {
            'weather_patterns': weather_patterns,
            'season_patterns': season_patterns,
            'temp_patterns': temp_patterns,
            'total_days': len(city_data)
        }
    
    def get_operation_suggestions(self, attraction_name, weather_forecast):
        """获取运营建议
        
        Args:
            attraction_name: 景点名称
            weather_forecast: 天气预报数据
            
        Returns:
            list: 运营建议列表
        """
        # 分析历史模式
        historical_patterns = self._analyze_historical_patterns(attraction_name)
        
        # 生成运营建议
        suggestions = []
        
        for forecast in weather_forecast:
            date = forecast['日期']
            weather = forecast['天气状况']
            temp = (forecast['最高气温'] + forecast['最低气温']) / 2
            
            # 基于历史模式生成建议
            day_suggestions = []
            
            # 分析天气状况
            if weather in historical_patterns['weather_patterns']:
                weather_stats = historical_patterns['weather_patterns'][weather]
                avg_traffic = weather_stats['avg_traffic']
                
                if avg_traffic > 1500:
                    # 高客流量情况
                    day_suggestions.extend([
                        '预计客流量较高，建议增加服务人员',
                        '提前准备充足的物资',
                        '考虑延长开放时间',
                        '加强景区内的安全巡逻'
                    ])
                elif avg_traffic < 800:
                    # 低客流量情况
                    day_suggestions.extend([
                        '预计客流量较低，可适当减少服务人员',
                        '考虑推出促销活动吸引游客',
                        '加强线上宣传',
                        '安排员工培训或设备维护'
                    ])
            
            # 分析温度情况
            if temp > 30:
                day_suggestions.extend([
                    '气温较高，建议增加遮阳设施',
                    '确保饮水设施充足',
                    '安排人员在高温时段巡逻，关注游客健康'
                ])
            elif temp < 0:
                day_suggestions.extend([
                    '气温较低，建议在入口处提供热水',
                    '提醒游客注意保暖',
                    '确保道路防滑措施到位'
                ])
            
            # 针对特殊天气的建议
            if '雨' in weather:
                day_suggestions.extend([
                    '准备雨具租赁服务',
                    '安排室内活动作为备选',
                    '确保排水系统正常运行',
                    '在景区入口处放置防滑垫'
                ])
            elif '雪' in weather:
                day_suggestions.extend([
                    '及时清理景区内的积雪',
                    '提醒游客穿防滑鞋',
                    '关闭部分危险路段'
                ])
            elif '雾' in weather:
                day_suggestions.extend([
                    '增加景区内的照明设施',
                    '提醒游客注意安全，保持适当距离',
                    '关闭部分视线不佳的景点'
                ])
            
            # 添加日期和建议
            suggestions.append({
                'date': date,
                'weather': weather,
                'temperature': temp,
                'suggestions': day_suggestions,
                'historical_reference': historical_patterns
            })
        
        return suggestions
    
    def analyze_traffic_trends(self, attraction_name, days=30):
        """分析客流量趋势
        
        Args:
            attraction_name: 景点名称
            days: 分析天数
            
        Returns:
            dict: 客流量趋势分析结果
        """
        # 加载历史数据
        historical_data = self._load_historical_data()
        
        # 获取景点所在城市
        attraction = self.attractions_df[self.attractions_df['景点名称'] == attraction_name]
        if attraction.empty:
            raise ValueError(f"景点 {attraction_name} 不存在")
        
        city = attraction.iloc[0]['城市']
        
        # 筛选该城市的数据
        city_data = historical_data[historical_data['城市'] == city]
        
        # 按日期排序
        city_data = city_data.sort_values('日期', ascending=False)
        
        # 取最近days天的数据
        recent_data = city_data.head(days)
        
        # 计算趋势
        recent_data['客流量移动平均'] = recent_data['客流量'].rolling(window=7).mean()
        
        # 计算日增长率
        recent_data['日增长率'] = recent_data['客流量'].pct_change() * 100
        
        # 分析结果
        trend_analysis = {
            'total_days': len(recent_data),
            'avg_traffic': int(recent_data['客流量'].mean()),
            'max_traffic': recent_data['客流量'].max(),
            'min_traffic': recent_data['客流量'].min(),
            'traffic_trend': '上升' if recent_data['客流量移动平均'].iloc[-1] > recent_data['客流量移动平均'].iloc[0] else '下降',
            'daily_data': recent_data[[
                '日期', '天气状况(白天)', '最高气温', '最低气温', 
                '客流量', '客流量移动平均', '日增长率'
            ]].to_dict('records')
        }
        
        return trend_analysis
    
    def generate_operation_report(self, attraction_name, weather_forecast):
        """生成运营分析报告
        
        Args:
            attraction_name: 景点名称
            weather_forecast: 天气预报数据
            
        Returns:
            dict: 运营分析报告
        """
        # 获取运营建议
        operation_suggestions = self.get_operation_suggestions(attraction_name, weather_forecast)
        
        # 分析客流量趋势
        traffic_trends = self.analyze_traffic_trends(attraction_name)
        
        # 生成报告
        report = {
            'attraction_name': attraction_name,
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'weather_forecast': weather_forecast,
            'operation_suggestions': operation_suggestions,
            'traffic_trends': traffic_trends,
            'summary': {
                'total_suggestions': sum(len(s['suggestions']) for s in operation_suggestions),
                'high_traffic_days': len([s for s in operation_suggestions if len(s['suggestions']) > 5]),
                'low_traffic_days': len([s for s in operation_suggestions if len(s['suggestions']) < 3])
            }
        }
        
        return report
    
    def get_weather_traffic_correlation(self, attraction_name):
        """获取天气与客流量的相关性分析
        
        Args:
            attraction_name: 景点名称
            
        Returns:
            dict: 相关性分析结果
        """
        # 加载历史数据
        historical_data = self._load_historical_data()
        
        # 获取景点所在城市
        attraction = self.attractions_df[self.attractions_df['景点名称'] == attraction_name]
        if attraction.empty:
            raise ValueError(f"景点 {attraction_name} 不存在")
        
        city = attraction.iloc[0]['城市']
        
        # 筛选该城市的数据
        city_data = historical_data[historical_data['城市'] == city]
        
        # 计算天气状况与客流量的相关性
        weather_corr = {}
        for weather in city_data['天气状况(白天)'].unique():
            weather_data = city_data[city_data['天气状况(白天)'] == weather]
            if len(weather_data) > 10:
                weather_corr[weather] = {
                    'avg_traffic': int(weather_data['客流量'].mean()),
                    'correlation': '正相关' if weather_data['客流量'].mean() > city_data['客流量'].mean() else '负相关',
                    'count': len(weather_data)
                }
        
        # 计算温度与客流量的相关性
        temp_corr = city_data[['平均气温', '客流量']].corr().iloc[0, 1]
        
        return {
            'weather_correlation': weather_corr,
            'temperature_correlation': temp_corr,
            'total_samples': len(city_data)
        }
