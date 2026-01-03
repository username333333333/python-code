from flask import Blueprint, render_template, request
from app.utils.data_loader import load_all_city_data
from app.services.recommendation_service import RecommendationService
import os
from app.config import Config
from flask_login import login_required

recommendation_view = Blueprint("recommendation", __name__, url_prefix="/recommendation")

@recommendation_view.route("/")
@login_required
def index():
    """旅游推荐主页"""
    try:
        # 加载所有天气数据
        weather_df = load_all_city_data()
        
        # 初始化推荐服务
        data_dir = os.path.abspath(Config.DATA_DIR)
        recommendation_service = RecommendationService(data_dir)
        
        # 获取请求参数
        city = request.args.get("city", "")
        date = request.args.get("date", "")
        recommendation_type = request.args.get("type", "weather")  # weather, season, type, search
        attraction_type = request.args.get("attraction_type", "")
        season = request.args.get("season", "")
        top_n = int(request.args.get("top_n", 5))
        
        # 搜索关键词
        search_keyword = request.args.get("search_keyword", "")
        
        # 新添加的筛选条件
        min_rating = float(request.args.get("min_rating", 0))
        max_price = request.args.get("max_price", None)
        max_price = float(max_price) if max_price and max_price.isdigit() else None
        
        # 处理门票类型筛选
        is_free = request.args.get("is_free", None)
        # 空字符串表示选择了"全部"选项，应视为不筛选
        if is_free == "":
            is_free = None
        else:
            is_free = is_free == "true" if is_free is not None else None
            
        selected_seasons = request.args.getlist("selected_seasons")
        
        # 获取可选值
        cities = recommendation_service.get_all_cities()
        attraction_types = recommendation_service.get_attraction_types()
        seasons = ['春季', '夏季', '秋季', '冬季']
        
        # 根据推荐类型获取推荐结果
        from pandas import DataFrame
        recommendations = DataFrame()
        
        # 搜索功能优先级最高
        if search_keyword:
            # 基于关键词搜索
            recommendations = recommendation_service.search_attractions(
                keyword=search_keyword,
                city=city,
                top_n=top_n
            )
        elif recommendation_type == "weather":
            # 基于天气推荐
            recommendations = recommendation_service.recommend_by_weather(
                weather_df, 
                city=city, 
                date=date, 
                top_n=top_n,
                min_rating=min_rating,
                max_price=max_price,
                is_free=is_free,
                seasons=selected_seasons
            )
        elif recommendation_type == "season" and season:
            # 基于季节推荐
            recommendations = recommendation_service.recommend_by_season(
                season, 
                city=city, 
                top_n=top_n,
                min_rating=min_rating,
                max_price=max_price,
                is_free=is_free
            )
        elif recommendation_type == "type" and attraction_type:
            # 基于景点类型推荐
            recommendations = recommendation_service.recommend_by_attraction_type(
                attraction_type, 
                city=city, 
                top_n=top_n,
                min_rating=min_rating,
                max_price=max_price,
                is_free=is_free,
                seasons=selected_seasons
            )
        else:
            # 默认推荐
            recommendations = recommendation_service.recommend_by_weather(
                weather_df, 
                city=city, 
                date=date, 
                top_n=top_n,
                min_rating=min_rating,
                max_price=max_price,
                is_free=is_free,
                seasons=selected_seasons
            )
        
        # 计算城市旅游评分
        city_scores = recommendation_service.calculate_city_travel_score(weather_df)
        
        # 处理推荐结果，确保可以正确序列化为JSON
        recommendations_dict = []
        if not recommendations.empty:
            recommendations_dict = recommendations.to_dict('records')
            # 进一步清洗数据，确保没有JSON序列化问题
            for rec in recommendations_dict:
                # 确保所有字符串值都是安全的
                for key, value in rec.items():
                    if isinstance(value, str):
                        # 去除无法正确序列化的特殊字符
                        import re
                        rec[key] = re.sub(r'[\x00-\x1f\x7f]', '', value)
        
        # 处理城市评分结果
        city_scores_dict = []
        if not city_scores.empty:
            city_scores_dict = city_scores.to_dict('records')
        
        return render_template(
            "recommendation.html",
            recommendations=recommendations_dict,
            cities=cities,
            attraction_types=attraction_types,
            seasons=seasons,
            city_scores=city_scores_dict,
            selected_city=city,
            selected_date=date,
            selected_type=recommendation_type,
            selected_attraction_type=attraction_type,
            selected_season=season,
            selected_top_n=top_n,
            selected_min_rating=min_rating,
            selected_max_price=max_price,
            selected_is_free=is_free,
            selected_selected_seasons=selected_seasons
        )
    except Exception as e:
        return render_template("error.html", message="推荐服务错误", details=str(e))

@recommendation_view.route("/city/<city_name>")
def city_recommendation(city_name):
    """城市旅游推荐"""
    try:
        # 加载所有天气数据
        weather_df = load_all_city_data()
        
        # 初始化推荐服务
        data_dir = os.path.abspath(Config.DATA_DIR)
        recommendation_service = RecommendationService(data_dir)
        
        # 获取城市景点
        attractions = recommendation_service.get_city_attractions(city_name, top_n=10)
        
        # 获取城市天气数据
        city_weather = weather_df[weather_df['城市'] == city_name]
        
        # 获取城市平均旅游评分
        avg_travel_score = city_weather['旅游评分'].mean() if not city_weather.empty else 0
        
        return render_template(
            "city_recommendation.html",
            city=city_name,
            attractions=attractions.to_dict('records'),
            avg_travel_score=round(avg_travel_score, 2),
            weather_data=city_weather.to_dict('records')[:30]  # 最近30天的天气数据
        )
    except Exception as e:
        return render_template("error.html", message=f"城市推荐错误: {city_name}", details=str(e))
