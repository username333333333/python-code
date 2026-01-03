from app.services.recommendation_service import RecommendationService
from app.utils.data_loader import load_all_city_data
import pandas as pd
from datetime import datetime, timedelta

class WeatherSensitiveRecommendationService:
    """天气敏感型景点推荐服务
    
    按景点对天气的敏感度分类，结合短期天气预测，给出适配天气的景点推荐
    """
    
    def __init__(self, data_dir):
        """初始化服务
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.recommendation_service = RecommendationService(data_dir)
        self.attraction_sensitivity = {
            # 景点类型: 敏感的天气因素列表
            '海滨': ['风力', '降水'],
            '滑雪': ['气温', '降雪'],
            '登山': ['降水', '风力', '能见度'],
            '博物馆': ['无特殊要求'],
            '温泉': ['气温'],
            '花海': ['气温', '降水'],
            '公园': ['气温', '降水'],
            '历史古迹': ['降水', '风力'],
            '主题乐园': ['气温', '降水'],
            '自然景观': ['降水', '风力', '能见度']
        }
    
    def get_weather_sensitive_recommendations(self, weather_forecast, days=7):
        """获取天气敏感型景点推荐
        
        Args:
            weather_forecast: 天气预报数据
            days: 推荐天数
            
        Returns:
            list: 每日推荐结果
        """
        recommendations = []
        
        # 加载所有景点数据
        attractions_df = self.recommendation_service.attractions_df
        
        for forecast in weather_forecast[:days]:
            date = forecast['date']
            weather = forecast['weather']
            temp = forecast['temperature']
            wind = forecast['wind']
            
            # 筛选适合当日天气的景点类型
            suitable_types = self._get_suitable_attraction_types(weather, temp, wind)
            
            # 根据筛选出的类型获取推荐景点
            day_recommendations = self._get_recommendations_by_types(
                attractions_df, suitable_types, date, top_n=5
            )
            
            recommendations.append({
                'date': date,
                'weather': weather,
                'temperature': temp,
                'wind': wind,
                'suitable_types': suitable_types,
                'recommendations': day_recommendations
            })
        
        return recommendations
    
    def _get_suitable_attraction_types(self, weather, temp, wind):
        """根据天气获取适合的景点类型
        
        Args:
            weather: 天气状况
            temp: 温度
            wind: 风力
            
        Returns:
            list: 适合的景点类型列表
        """
        suitable_types = []
        
        # 根据天气状况推荐
        if weather == '晴' or weather == '多云':
            if temp > 20:
                suitable_types.extend(['海滨', '公园', '花海', '主题乐园'])
            elif temp > 0:
                suitable_types.extend(['登山', '历史古迹', '自然景观'])
            else:
                suitable_types.extend(['温泉'])
        elif weather == '雨':
            suitable_types.extend(['博物馆', '主题乐园'])
        elif '雪' in weather:
            suitable_types.extend(['滑雪', '温泉'])
        elif '雾' in weather:
            suitable_types.extend(['博物馆', '室内景点'])
        
        # 风力考虑
        if wind > 5:
            # 大风天气不推荐海滨和登山
            suitable_types = [t for t in suitable_types if t not in ['海滨', '登山']]
        
        # 高温考虑
        if temp > 35:
            # 高温天气推荐室内景点
            suitable_types.extend(['博物馆', '室内景点'])
        
        return list(set(suitable_types))
    
    def _get_recommendations_by_types(self, attractions_df, types, date, top_n=5):
        """根据景点类型获取推荐
        
        Args:
            attractions_df: 景点数据
            types: 景点类型列表
            date: 日期
            top_n: 推荐数量
            
        Returns:
            list: 推荐景点列表
        """
        if attractions_df.empty or not types:
            return []
        
        # 筛选符合类型的景点
        filtered_attractions = attractions_df.copy()
        
        # 景点类型匹配
        type_mask = filtered_attractions['景点类型'].isin(types) | filtered_attractions['景点类型'].str.contains('|'.join(types))
        filtered_attractions = filtered_attractions[type_mask]
        
        # 按评分排序
        filtered_attractions = filtered_attractions.sort_values('评分', ascending=False)
        
        # 限制结果数量
        filtered_attractions = filtered_attractions.head(top_n)
        
        # 转换为字典列表
        # 检查'开放时间'列是否存在
        columns = ['景点名称', '城市', '评分', '景点类型', '简介', '门票价格']
        if '开放时间' in filtered_attractions.columns:
            columns.append('开放时间')
        
        recommendations = filtered_attractions[columns].to_dict('records')
        
        return recommendations
    
    def get_attraction_type_sensitivity(self, attraction_type):
        """获取景点类型对天气的敏感度
        
        Args:
            attraction_type: 景点类型
            
        Returns:
            list: 敏感的天气因素列表
        """
        return self.attraction_sensitivity.get(attraction_type, ['无特殊要求'])
    
    def recommend_for_specific_attraction(self, attraction_name, weather_forecast):
        """为特定景点推荐适合的出行日期
        
        Args:
            attraction_name: 景点名称
            weather_forecast: 天气预报数据
            
        Returns:
            list: 适合的出行日期列表
        """
        # 加载所有景点数据
        attractions_df = self.recommendation_service.attractions_df
        
        # 查找景点
        attraction = attractions_df[attractions_df['景点名称'] == attraction_name]
        if attraction.empty:
            return []
        
        attraction_type = attraction.iloc[0]['类型']
        sensitivity = self.get_attraction_type_sensitivity(attraction_type)
        
        # 根据敏感度筛选适合的日期
        suitable_dates = []
        
        for forecast in weather_forecast:
            date = forecast['date']
            weather = forecast['weather']
            temp = forecast['temperature']
            wind = forecast['wind']
            
            # 检查是否适合
            if self._is_suitable_for_attraction_type(
                attraction_type, weather, temp, wind
            ):
                suitable_dates.append({
                    'date': date,
                    'weather': weather,
                    'temperature': temp,
                    'wind': wind,
                    'suitable': True
                })
        
        return suitable_dates
    
    def _is_suitable_for_attraction_type(self, attraction_type, weather, temp, wind):
        """检查天气是否适合特定景点类型
        
        Args:
            attraction_type: 景点类型
            weather: 天气状况
            temp: 温度
            wind: 风力
            
        Returns:
            bool: 是否适合
        """
        sensitivity = self.get_attraction_type_sensitivity(attraction_type)
        
        if '无特殊要求' in sensitivity:
            return True
        
        # 根据敏感度检查
        if '降水' in sensitivity and ('雨' in weather or '雪' in weather):
            return False
        
        if '风力' in sensitivity and wind > 5:
            return False
        
        if '气温' in sensitivity:
            if attraction_type == '滑雪' and temp > 0:
                return False
            if attraction_type == '温泉' and temp > 25:
                return False
            if attraction_type == '花海' and (temp < 10 or temp > 30):
                return False
        
        return True
    
    def get_weather_sensitivity_report(self, attraction_type):
        """获取景点类型的天气敏感度报告
        
        Args:
            attraction_type: 景点类型
            
        Returns:
            dict: 敏感度报告
        """
        sensitivity = self.get_attraction_type_sensitivity(attraction_type)
        
        report = {
            'attraction_type': attraction_type,
            'sensitive_factors': sensitivity,
            'recommendations': []
        }
        
        # 根据敏感度给出推荐
        if '降水' in sensitivity:
            report['recommendations'].append('雨天不推荐出行，建议选择其他室内活动')
        
        if '风力' in sensitivity:
            report['recommendations'].append('大风天气不推荐出行，风力超过5级需谨慎')
        
        if '气温' in sensitivity:
            if attraction_type == '滑雪':
                report['recommendations'].append('滑雪景点适合气温低于0℃的天气')
            elif attraction_type == '温泉':
                report['recommendations'].append('温泉景点适合气温较低的天气')
            elif attraction_type == '花海':
                report['recommendations'].append('花海景点适合气温10-30℃的天气')
        
        if '能见度' in sensitivity:
            report['recommendations'].append('大雾天气不推荐出行，能见度低影响体验')
        
        return report