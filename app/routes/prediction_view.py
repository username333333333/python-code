from flask import Blueprint, render_template, request
from app.utils.data_loader import load_all_city_data
from app.services.prediction_service import WeatherPredictionService
from app.services.recommendation_service import RecommendationService
import os
from app.config import Config
from flask_login import login_required

prediction_view = Blueprint("prediction", __name__, url_prefix="/prediction")

@prediction_view.route("/")
@login_required
def index():
    """天气预测主页"""
    try:
        # 加载所有天气数据
        weather_df = load_all_city_data()
        
        # 初始化服务 - 使用工厂模式，便于未来切换到Spark实现
        data_dir = os.path.abspath(Config.DATA_DIR)
        from app.services.prediction_service import WeatherPredictionServiceFactory
        prediction_service = WeatherPredictionServiceFactory.create_service(service_type="sklearn", data_dir=data_dir)
        recommendation_service = RecommendationService(data_dir)
        
        # 获取请求参数
        city = request.args.get("city", "沈阳")
        days = int(request.args.get("days", 7))
        
        # 尝试直接预测，避免每次都训练模型
        predictions = prediction_service.predict_future(weather_df, city, days)
        
        # 如果预测失败（模型不存在），再训练模型并重新预测
        if predictions.empty:
            training_results = prediction_service.train_all_models(weather_df)
            predictions = prediction_service.predict_future(weather_df, city, days)
        else:
            training_results = {}
        
        
        # 获取城市列表
        cities = sorted(weather_df['城市'].unique())
        
        # 如果有预测结果，基于预测结果提供旅游推荐
        if not predictions.empty:
            # 获取推荐服务
            recommendation_service = RecommendationService(data_dir)
            # 基于预测天气推荐景点
            future_recommendations = []
            for _, row in predictions.iterrows():
                # 为每天生成推荐
                date_str = row['日期'].strftime('%Y-%m-%d')
                day_recommendations = recommendation_service.recommend_by_weather(
                    weather_df, city=city, date=date_str, top_n=3
                )
                future_recommendations.append({
                    'date': date_str,
                    'recommendations': day_recommendations.to_dict('records')
                })
        else:
            future_recommendations = []
        
        return render_template(
            "prediction.html",
            predictions=predictions.to_dict('records') if not predictions.empty else [],
            future_recommendations=future_recommendations,
            cities=cities,
            selected_city=city,
            selected_days=days,
            training_results=training_results
        )
    except Exception as e:
        return render_template("error.html", message="预测服务错误", details=str(e))

@prediction_view.route("/all_cities")
def all_cities_prediction():
    """所有城市天气预测"""
    try:
        # 加载所有天气数据
        weather_df = load_all_city_data()
        
        # 初始化预测服务和推荐服务
        data_dir = os.path.abspath(Config.DATA_DIR)
        prediction_service = WeatherPredictionService(data_dir)
        recommendation_service = RecommendationService(data_dir)
        
        # 获取请求参数
        days = int(request.args.get("days", 7))
        selected_city = request.args.get("city", None)
        
        # 尝试直接预测所有城市，避免每次都训练模型
        all_predictions = prediction_service.predict_all_cities(weather_df, days)
        
        # 如果预测失败（模型不存在），再训练模型并重新预测
        if not all_predictions or len(all_predictions) == 0:
            # 只训练选定城市的模型，而不是所有城市
            if selected_city:
                # 只训练选定城市的模型
                city_weather_df = weather_df[weather_df['城市'] == selected_city]
                if not city_weather_df.empty:
                    # 创建临时的单城市天气数据
                    temp_weather_df = weather_df[weather_df['城市'] == selected_city]
                    # 训练单城市模型
                    prediction_service.train_all_models(temp_weather_df)
                    # 预测单城市
                    all_predictions = {
                        selected_city: prediction_service.predict_future(temp_weather_df, selected_city, days)
                    }
            else:
                # 如果没有选择城市，才训练所有城市模型
                prediction_service.train_all_models(weather_df)
                all_predictions = prediction_service.predict_all_cities(weather_df, days)
        
        # 为每个城市生成景点推荐
        city_recommendations = {}
        
        for city, df in all_predictions.items():
            # 为每个城市生成景点推荐，优化性能
            daily_recommendations = []
            if not df.empty:
                # 优化：使用缓存机制，避免重复生成推荐
                import pickle
                from pathlib import Path
                cache_dir = Path(Config.DATA_DIR) / 'cache'
                cache_dir.mkdir(exist_ok=True)
                
                # 为该城市的推荐创建缓存文件路径
                cache_file = cache_dir / f"recommendations_{city}_{days}days.pkl"
                
                # 尝试从缓存加载推荐结果
                if cache_file.exists():
                    try:
                        with open(cache_file, 'rb') as f:
                            daily_recommendations = pickle.load(f)
                        print(f"从缓存加载{city}的推荐结果")
                    except Exception as e:
                        print(f"加载推荐缓存失败: {e}")
                        daily_recommendations = []
                
                # 如果缓存不存在或加载失败，生成新的推荐
                if not daily_recommendations:
                    # 为每个城市的每天生成推荐，但限制生成的天数
                    max_days_to_generate = min(days, 7)  # 最多生成7天的推荐，减少计算量
                    for i, (_, row) in enumerate(df.iterrows()):
                        if i >= max_days_to_generate:
                            # 对于剩余天数，重复使用前7天的推荐或跳过
                            break
                        
                        date_str = row['日期'].strftime('%Y-%m-%d')
                        recommendations = recommendation_service.recommend_by_weather(
                            weather_df, city=city, date=date_str, top_n=3
                        )
                        daily_recommendations.append({
                            'date': date_str,
                            'recommendations': recommendations.to_dict('records')
                        })
                    
                    # 将推荐结果保存到缓存
                    try:
                        with open(cache_file, 'wb') as f:
                            pickle.dump(daily_recommendations, f)
                        print(f"保存{city}的推荐结果到缓存")
                    except Exception as e:
                        print(f"保存推荐缓存失败: {e}")
            city_recommendations[city] = daily_recommendations
        
        # 获取城市列表
        cities = sorted(weather_df['城市'].unique())
        
        return render_template(
            "all_cities_prediction.html",
            all_predictions=all_predictions,
            city_recommendations=city_recommendations,
            selected_days=days,
            cities=cities,
            selected_city=selected_city
        )
    except Exception as e:
        return render_template("error.html", message="所有城市预测服务错误", details=str(e))
