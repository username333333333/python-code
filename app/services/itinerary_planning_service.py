from app.services.recommendation_service import RecommendationService
from app.services.risk_assessment_service import RiskAssessmentService
from app.utils.data_loader import load_all_city_data
import pandas as pd
from datetime import datetime, timedelta

class ItineraryPlanningService:
    """个性化行程规划服务
    
    基于用户偏好和天气预测数据，自动生成多日旅游行程方案
    """
    
    def __init__(self, data_dir):
        """初始化服务
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.recommendation_service = RecommendationService(data_dir)
        self.risk_assessment_service = RiskAssessmentService(data_dir)
        
        # 加载所有景点数据
        self.attractions_df = self.recommendation_service.attractions_df
        
        # 景点类型权重映射（用于个性化推荐）
        self.type_weights = {
            '山地': 0,
            '海滨': 0,
            '博物馆': 0,
            '主题乐园': 0,
            '温泉': 0,
            '滑雪': 0,
            '公园': 0,
            '历史古迹': 0,
            '自然景观': 0,
            '户外': 0
        }
    
    def plan_itinerary(self, user_preferences, weather_forecast, start_date=None, days=3):
        """生成个性化行程
        
        Args:
            user_preferences: 用户偏好
                - preferred_types: 偏好的景点类型列表
                - temp_preference: 温度偏好（'warm', 'cool', 'any'）
                - activity_level: 活动强度（'low', 'medium', 'high'）
                - budget: 预算等级（'low', 'medium', 'high'）
                - travel_style: 旅行风格（'relaxing', 'adventurous', 'cultural'）
            weather_forecast: 天气预报数据
            start_date: 行程开始日期
            days: 行程天数
            
        Returns:
            dict: 行程规划结果
        """
        # 设置默认开始日期
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        
        # 解析开始日期
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        # 生成每日日期列表
        itinerary_dates = [start_date + timedelta(days=i) for i in range(days)]
        itinerary_dates_str = [d.strftime('%Y-%m-%d') for d in itinerary_dates]
        
        # 计算用户偏好权重
        self._calculate_preference_weights(user_preferences)
        
        # 初始化行程规划结果
        itinerary = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'days': days,
            'user_preferences': user_preferences,
            'daily_plans': []
        }
        
        # 为每天生成行程
        for i, date in enumerate(itinerary_dates):
            date_str = date.strftime('%Y-%m-%d')
            
            # 获取当日天气预报
            day_forecast = next(
                (f for f in weather_forecast if f['date'] == date_str),
                None
            )
            
            if not day_forecast:
                # 如果没有当日天气预报，跳过
                continue
            
            # 获取当日推荐景点
            daily_recommendations = self._get_daily_recommendations(
                user_preferences, day_forecast, date_str
            )
            
            # 生成当日行程
            daily_plan = self._generate_daily_plan(
                daily_recommendations, day_forecast, user_preferences, i+1
            )
            
            itinerary['daily_plans'].append(daily_plan)
        
        return itinerary
    
    def _calculate_preference_weights(self, user_preferences):
        """计算用户偏好权重
        
        Args:
            user_preferences: 用户偏好
        """
        # 重置权重
        for key in self.type_weights:
            self.type_weights[key] = 0
        
        # 设置偏好类型权重
        if 'preferred_types' in user_preferences and user_preferences['preferred_types']:
            for preferred_type in user_preferences['preferred_types']:
                if preferred_type in self.type_weights:
                    self.type_weights[preferred_type] = 1.0
        
        # 根据旅行风格调整权重
        if 'travel_style' in user_preferences:
            travel_style = user_preferences['travel_style']
            if travel_style == 'relaxing':
                self.type_weights['海滨'] += 0.5
                self.type_weights['温泉'] += 0.5
                self.type_weights['公园'] += 0.3
            elif travel_style == 'adventurous':
                self.type_weights['山地'] += 0.5
                self.type_weights['户外'] += 0.5
                self.type_weights['自然景观'] += 0.3
            elif travel_style == 'cultural':
                self.type_weights['博物馆'] += 0.5
                self.type_weights['历史古迹'] += 0.5
                self.type_weights['主题乐园'] += 0.3
    
    def _get_daily_recommendations(self, user_preferences, day_forecast, date):
        """获取每日推荐景点
        
        Args:
            user_preferences: 用户偏好
            day_forecast: 当日天气预报
            date: 日期
            
        Returns:
            list: 当日推荐景点列表
        """
        # 获取适合当日天气的景点类型
        weather = day_forecast['weather']
        temp = day_forecast['temperature']
        wind = day_forecast['wind']
        
        # 基于天气和用户偏好获取推荐
        filtered_attractions = self.attractions_df.copy()
        
        # 根据温度偏好筛选
        if 'temp_preference' in user_preferences:
            temp_preference = user_preferences['temp_preference']
            if temp_preference == 'warm' and temp < 15:
                # 温暖偏好，温度低于15℃，推荐室内景点
                filtered_attractions = filtered_attractions[filtered_attractions['景点类型'].isin(['博物馆', '温泉', '主题乐园'])]
            elif temp_preference == 'cool' and temp > 25:
                # 凉爽偏好，温度高于25℃，推荐水上或室内景点
                filtered_attractions = filtered_attractions[filtered_attractions['景点类型'].isin(['海滨', '博物馆', '主题乐园'])]
        
        # 根据预算筛选
        if 'budget' in user_preferences:
            budget = user_preferences['budget']
            if budget == 'low':
                # 低预算，推荐免费或低价景点
                filtered_attractions = filtered_attractions[filtered_attractions['门票价格'] <= 50]
            elif budget == 'high':
                # 高预算，不限制
                pass
            else:  # medium
                # 中等预算，限制门票价格
                filtered_attractions = filtered_attractions[filtered_attractions['门票价格'] <= 150]
        
        # 根据活动强度筛选
        if 'activity_level' in user_preferences:
            activity_level = user_preferences['activity_level']
            if activity_level == 'low':
                # 低活动强度，推荐轻松的景点
                filtered_attractions = filtered_attractions[filtered_attractions['景点类型'].isin(['博物馆', '海滨', '温泉', '公园'])]
            elif activity_level == 'high':
                # 高活动强度，推荐活动量大的景点
                filtered_attractions = filtered_attractions[filtered_attractions['景点类型'].isin(['山地', '户外', '自然景观', '主题乐园'])]
        
        # 应用景点类型权重
        filtered_attractions['score'] = filtered_attractions['评分'] * filtered_attractions['景点类型'].apply(
            lambda x: self.type_weights.get(x, 0.5)
        )
        
        # 按评分排序
        filtered_attractions = filtered_attractions.sort_values('score', ascending=False)
        
        # 限制结果数量
        top_attractions = filtered_attractions.head(10)
        
        return top_attractions.to_dict('records')
    
    def _generate_daily_plan(self, recommendations, day_forecast, user_preferences, day_number):
        """生成每日行程计划
        
        Args:
            recommendations: 推荐景点列表
            day_forecast: 当日天气预报
            user_preferences: 用户偏好
            day_number: 行程天数
            
        Returns:
            dict: 每日行程计划
        """
        # 从推荐景点中选择3-5个景点安排行程
        selected_attractions = recommendations[:5]
        
        # 生成行程时间安排
        schedule = self._generate_schedule(selected_attractions, day_forecast)
        
        # 生成每日行程计划
        daily_plan = {
            'day': day_number,
            'date': day_forecast['date'],
            'weather': day_forecast['weather'],
            'temperature': day_forecast['temperature'],
            'wind': day_forecast['wind'],
            'schedule': schedule,
            'recommended_attractions': selected_attractions,
            'tips': self._generate_daily_tips(day_forecast, user_preferences)
        }
        
        return daily_plan
    
    def _generate_schedule(self, attractions, day_forecast):
        """生成行程时间安排
        
        Args:
            attractions: 当日推荐景点
            day_forecast: 当日天气预报
            
        Returns:
            list: 行程时间安排
        """
        # 简单的时间安排，假设每天从9:00开始，每两个小时一个景点
        schedule = []
        start_hour = 9
        
        for i, attraction in enumerate(attractions):
            if i >= 3:  # 每天最多安排3个主要景点
                break
            
            # 计算景点时间
            start_time = f'{start_hour:02d}:00'
            end_time = f'{start_hour+2:02d}:00'
            
            schedule.append({
                'time_slot': f'{start_time} - {end_time}',
                'attraction': attraction,
                'activity': f'游览{attraction["景点名称"]}',
                'recommended_transport': '公交/地铁' if i > 0 else '步行'
            })
            
            # 增加休息时间
            start_hour += 3
        
        # 添加午餐时间
        if schedule:
            schedule.insert(1, {
                'time_slot': '12:00 - 13:00',
                'activity': '午餐',
                'recommended_transport': '步行'
            })
        
        return schedule
    
    def _generate_daily_tips(self, day_forecast, user_preferences):
        """生成每日出行建议
        
        Args:
            day_forecast: 当日天气预报
            user_preferences: 用户偏好
            
        Returns:
            list: 出行建议列表
        """
        tips = []
        
        # 天气相关建议
        weather = day_forecast['weather']
        temp = day_forecast['temperature']
        wind = day_forecast['wind']
        
        if '雨' in weather:
            tips.append('今日有雨，建议携带雨伞和穿防水鞋')
        
        if temp > 30:
            tips.append('今日气温较高，注意防暑降温，携带足够的水')
        elif temp < 10:
            tips.append('今日气温较低，注意保暖，穿厚外套')
        
        if wind > 5:
            tips.append('今日风力较大，注意防风，避免在户外长时间停留')
        
        # 活动强度相关建议
        if 'activity_level' in user_preferences and user_preferences['activity_level'] == 'high':
            tips.append('今日活动强度较大，建议穿着舒适的运动鞋')
        
        # 旅行风格相关建议
        if 'travel_style' in user_preferences:
            travel_style = user_preferences['travel_style']
            if travel_style == 'relaxing':
                tips.append('建议放慢脚步，享受轻松的旅行时光')
            elif travel_style == 'adventurous':
                tips.append('今日行程充满挑战，注意安全，听从向导建议')
            elif travel_style == 'cultural':
                tips.append('建议提前了解景点的历史背景，增强游览体验')
        
        return tips
    
    def optimize_itinerary(self, initial_itinerary, weather_forecast):
        """优化行程
        
        Args:
            initial_itinerary: 初始行程
            weather_forecast: 天气预报数据
            
        Returns:
            dict: 优化后的行程
        """
        # 简单的行程优化，主要是根据天气预报调整行程顺序
        optimized_itinerary = initial_itinerary.copy()
        
        # 这里可以添加更复杂的优化算法，如遗传算法、贪心算法等
        # 目前实现一个简单的基于天气的优化
        
        # 按天气状况调整每日景点安排
        for day_plan in optimized_itinerary['daily_plans']:
            date = day_plan['date']
            forecast = next(
                (f for f in weather_forecast if f['date'] == date),
                None
            )
            
            if forecast and '雨' in forecast['weather']:
                # 雨天，将户外活动调整为室内活动
                indoor_attractions = [
                    att for att in day_plan['recommended_attractions']
                    if att['景点类型'] in ['博物馆', '主题乐园', '温泉']
                ]
                
                if indoor_attractions:
                    day_plan['recommended_attractions'] = indoor_attractions
                    day_plan['schedule'] = self._generate_schedule(indoor_attractions, forecast)
        
        return optimized_itinerary
    
    def generate_travel_report(self, itinerary):
        """生成旅行报告
        
        Args:
            itinerary: 行程规划结果
            
        Returns:
            dict: 旅行报告
        """
        # 计算行程统计信息
        total_attractions = sum(
            len(day['recommended_attractions']) 
            for day in itinerary['daily_plans']
        )
        
        attraction_types = []
        for day in itinerary['daily_plans']:
            for attraction in day['recommended_attractions']:
                attraction_types.append(attraction['景点类型'])
        
        # 生成报告
        report = {
            'itinerary': itinerary,
            'statistics': {
                'total_days': itinerary['days'],
                'total_attractions': total_attractions,
                'attraction_types': list(set(attraction_types)),
                'avg_attractions_per_day': total_attractions / itinerary['days']
            },
            'recommendation': '根据您的偏好和天气情况，这是为您定制的个性化行程建议。'
        }
        
        return report