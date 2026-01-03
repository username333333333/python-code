from flask import Blueprint, render_template, request
from app.utils.data_loader import load_all_city_data
from app.services.recommendation_service import RecommendationService
from app.services.path_optimization_service import PathOptimizationService
from app.services.traffic_prediction_service import TrafficPredictionService
from app.services.risk_assessment_service import RiskAssessmentService
import os
from app.config import Config
from flask_login import login_required

tourism_decision_center = Blueprint("tourism_decision_center", __name__, url_prefix="/decision-center")

@tourism_decision_center.route("/")
@login_required
def index():
    """旅游决策中心主页"""
    try:
        # 加载所有天气数据
        weather_df = load_all_city_data()
        
        # 初始化各服务
        data_dir = os.path.abspath(Config.DATA_DIR)
        recommendation_service = RecommendationService(data_dir)
        path_service = PathOptimizationService()
        traffic_service = TrafficPredictionService(data_dir)
        risk_service = RiskAssessmentService(data_dir)
        
        # 获取请求参数
        selected_city = request.args.get("selected_city", "")
        travel_date = request.args.get("travel_date", "")
        attraction_type = request.args.getlist("attraction_type")
        min_rating = float(request.args.get("min_rating", 4.0))
        show_recommendations = request.args.get("show_recommendations", "false") == "true"
        
        # 获取可选值
        cities = recommendation_service.get_all_cities()
        attraction_types = recommendation_service.get_attraction_types()
        
        # 计算城市推荐指数，传递travel_date参数
        city_scores = recommendation_service.calculate_city_travel_score(weather_df, travel_date)
        city_scores_dict = []
        if not city_scores.empty:
            city_scores_dict = city_scores.to_dict('records')
            
            # 为每个城市添加天气情况和预计客流量
            for city in city_scores_dict:
                city_name = city['城市']
                
                if travel_date:
                    # 尝试获取指定日期的天气数据
                    try:
                        from datetime import datetime
                        travel_date_obj = datetime.strptime(travel_date, '%Y-%m-%d')
                        
                        # 统一城市名称格式：尝试带'市'字和不带'市'字两种格式
                        city_name_with_suffix = city_name + '市' if not city_name.endswith('市') else city_name
                        city_name_without_suffix = city_name.replace('市', '') if city_name.endswith('市') else city_name
                        
                        # 尝试多种日期匹配策略
                        date_weather = None
                        
                        # 1. 精确匹配：指定城市和日期
                        exact_match = weather_df[(weather_df['日期'] == travel_date_obj) & ((weather_df['城市'] == city_name_with_suffix) | (weather_df['城市'] == city_name_without_suffix))]
                        
                        if not exact_match.empty:
                            date_weather = exact_match
                        else:
                            # 2. 年份模糊匹配：使用相同月份和日期，任意年份的数据
                            month = travel_date_obj.month
                            day = travel_date_obj.day
                            same_month_day = weather_df[(weather_df['日期'].dt.month == month) & (weather_df['日期'].dt.day == day) & ((weather_df['城市'] == city_name_with_suffix) | (weather_df['城市'] == city_name_without_suffix))]
                            if not same_month_day.empty:
                                # 使用固定随机种子，确保相同日期下返回相同的天气数据
                                import random
                                random.seed(f"{city_name}-{month}-{day}")
                                date_weather = same_month_day.sample(1, random_state=random.randint(0, 10000))
                        
                        if date_weather is not None and not date_weather.empty:
                            # 使用匹配到的天气数据
                            city_weather_data = date_weather.iloc[0]
                            city['天气'] = city_weather_data.get('天气状况(白天)', city_weather_data.get('天气状况', '晴'))
                            city['温度'] = city_weather_data.get('平均气温', '未知')
                            city['风力'] = city_weather_data.get('风力(白天)_数值', '未知')
                            
                            # 根据天气和评分计算预计客流量
                            weather = city['天气'].lower()
                            rating = city['平均旅游评分']
                            
                            # 基于天气状况调整客流量
                            weather_factor = 1.0
                            if '雨' in weather or '雪' in weather or '雾' in weather:
                                weather_factor = 0.6  # 恶劣天气减少客流量
                            elif '晴' in weather:
                                weather_factor = 1.2  # 晴天增加客流量
                            elif '多云' in weather:
                                weather_factor = 1.0  # 多云正常
                            
                            # 计算综合客流量指数
                            traffic_index = rating * weather_factor
                            
                            if traffic_index >= 90:
                                city['预计客流量'] = '较多'
                            elif traffic_index >= 70:
                                city['预计客流量'] = '适中'
                            else:
                                city['预计客流量'] = '较少'
                        else:
                            # 如果没有匹配到数据，使用基于季节的合理默认值
                            month = travel_date_obj.month
                            # 根据月份设置不同的默认天气
                            if month in [12, 1, 2]:
                                # 冬季
                                city['天气'] = '多云'
                                city['温度'] = '-5°'
                                city['风力'] = '4级'
                            elif month in [3, 4, 5]:
                                # 春季
                                city['天气'] = '晴'
                                city['温度'] = '15°'
                                city['风力'] = '3级'
                            elif month in [6, 7, 8]:
                                # 夏季
                                city['天气'] = '晴'
                                city['温度'] = '28°'
                                city['风力'] = '2级'
                            else:
                                # 秋季
                                city['天气'] = '多云'
                                city['温度'] = '10°'
                                city['风力'] = '3级'
                            
                            # 根据评分生成预计客流量
                            if city['平均旅游评分'] >= 90:
                                city['预计客流量'] = '较多'
                            elif city['平均旅游评分'] >= 70:
                                city['预计客流量'] = '适中'
                            else:
                                city['预计客流量'] = '较少'
                    except ValueError as e:
                        # 日期解析失败，使用基于当前季节的默认值
                        from datetime import datetime
                        current_month = datetime.now().month
                        if current_month in [12, 1, 2]:
                            # 冬季
                            city['天气'] = '多云'
                            city['温度'] = '-5°'
                            city['风力'] = '4级'
                        elif current_month in [3, 4, 5]:
                            # 春季
                            city['天气'] = '晴'
                            city['温度'] = '15°'
                            city['风力'] = '3级'
                        elif current_month in [6, 7, 8]:
                            # 夏季
                            city['天气'] = '晴'
                            city['温度'] = '28°'
                            city['风力'] = '2级'
                        else:
                            # 秋季
                            city['天气'] = '多云'
                            city['温度'] = '10°'
                            city['风力'] = '3级'
                        
                        # 根据评分生成预计客流量
                        if city['平均旅游评分'] >= 90:
                            city['预计客流量'] = '较多'
                        elif city['平均旅游评分'] >= 70:
                            city['预计客流量'] = '适中'
                        else:
                            city['预计客流量'] = '较少'
                else:
                    # 没有指定日期，使用基于当前季节的默认值
                    from datetime import datetime
                    current_month = datetime.now().month
                    if current_month in [12, 1, 2]:
                        # 冬季
                        city['天气'] = '多云'
                        city['温度'] = '-5°'
                        city['风力'] = '4级'
                    elif current_month in [3, 4, 5]:
                        # 春季
                        city['天气'] = '晴'
                        city['温度'] = '15°'
                        city['风力'] = '3级'
                    elif current_month in [6, 7, 8]:
                        # 夏季
                        city['天气'] = '晴'
                        city['温度'] = '28°'
                        city['风力'] = '2级'
                    else:
                        # 秋季
                        city['天气'] = '多云'
                        city['温度'] = '10°'
                        city['风力'] = '3级'
                    
                    # 根据评分生成预计客流量
                    if city['平均旅游评分'] >= 90:
                        city['预计客流量'] = '较多'
                    elif city['平均旅游评分'] >= 70:
                        city['预计客流量'] = '适中'
                    else:
                        city['预计客流量'] = '较少'
        
        # 获取景点推荐
        recommendations = []
        if selected_city:
            # 根据城市和类型获取推荐景点
            recommendations_df = recommendation_service.recommend_by_weather(
                weather_df, 
                city=selected_city, 
                date=travel_date, 
                top_n=10,
                min_rating=min_rating,
                attraction_types=attraction_type
            )
            if not recommendations_df.empty:
                recommendations = recommendations_df.to_dict('records')
                # 清洗数据
                for rec in recommendations:
                    import re
                    for key, value in rec.items():
                        if isinstance(value, str):
                            rec[key] = re.sub(r'[\x00-\x1f\x7f]', '', value)
            else:
                recommendations = []
        
        return render_template(
            "tourism_decision_center.html",
            cities=cities,
            attraction_types=attraction_types,
            city_scores=city_scores_dict,
            recommendations=recommendations,
            selected_city=selected_city,
            travel_date=travel_date,
            selected_attraction_types=attraction_type,
            show_recommendations=show_recommendations
        )
    except Exception as e:
        return render_template("error.html", message="旅游决策中心错误", details=str(e))