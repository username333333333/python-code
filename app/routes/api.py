from flask import Blueprint, request, jsonify
from app.services.traffic_prediction_service import TrafficPredictionService
from app.services.risk_assessment_service import RiskAssessmentService
from app.services.itinerary_planning_service import ItineraryPlanningService
from app.services.prediction_service import WeatherPredictionService
from app.services.path_optimization_service import PathOptimizationService
from app.services.map_service import MapService
from app.utils.data_loader import load_all_city_data
import os
from app.config import Config
from flask_login import login_required

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route('/traffic_prediction/predict', methods=['POST'])
def predict_traffic():
    """预测景点客流量"""
    try:
        # 获取请求数据
        data = request.get_json()
        attraction_name = data.get('attraction_name')
        weather_forecast = data.get('weather_forecast')
        is_holiday = data.get('is_holiday', False)
        
        if not attraction_name:
            return jsonify({
                'success': False,
                'message': '景点名称不能为空'
            }), 400
        
        if not weather_forecast:
            return jsonify({
                'success': False,
                'message': '天气预报数据不能为空'
            }), 400
        
        # 初始化服务
        data_dir = os.path.abspath(Config.DATA_DIR)
        traffic_service = TrafficPredictionService(data_dir)
        
        # 预测客流量
        predictions = traffic_service.predict_future_traffic(
            attraction_name, weather_forecast, is_holiday
        )
        
        return jsonify({
            'success': True,
            'prediction': predictions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'客流量预测失败: {str(e)}'
        }), 500

@api_bp.route('/risk_assessment/assess', methods=['POST'])
def assess_risk():
    """评估出行风险"""
    try:
        # 获取请求数据
        data = request.get_json()
        attraction_name = data.get('attraction_name')
        attraction_desc = data.get('attraction_desc', '')
        weather_forecast = data.get('weather_forecast')
        
        if not attraction_name:
            return jsonify({
                'success': False,
                'message': '景点名称不能为空'
            }), 400
        
        if not weather_forecast:
            return jsonify({
                'success': False,
                'message': '天气预报数据不能为空'
            }), 400
        
        # 初始化服务
        data_dir = os.path.abspath(Config.DATA_DIR)
        risk_service = RiskAssessmentService(data_dir)
        
        # 生成风险评估报告
        risk_report = risk_service.generate_risk_report(
            attraction_name, attraction_desc, weather_forecast
        )
        
        return jsonify({
            'success': True,
            'risk_result': risk_report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'风险评估失败: {str(e)}'
        }), 500

@api_bp.route('/itinerary_planning/plan', methods=['POST'])
def plan_itinerary():
    """生成个性化行程"""
    try:
        # 获取请求数据
        data = request.get_json()
        user_preferences = data.get('preferences', {})
        weather_forecast = data.get('weather_forecast')
        start_date = data.get('start_date')
        days = int(data.get('days', 3))
        
        if not weather_forecast:
            return jsonify({
                'success': False,
                'message': '天气预报数据不能为空'
            }), 400
        
        # 初始化服务
        data_dir = os.path.abspath(Config.DATA_DIR)
        itinerary_service = ItineraryPlanningService(data_dir)
        
        # 生成行程
        itinerary = itinerary_service.plan_itinerary(
            user_preferences, weather_forecast, start_date, days
        )
        
        # 优化行程
        optimized_itinerary = itinerary_service.optimize_itinerary(
            itinerary, weather_forecast
        )
        
        # 生成旅行报告
        travel_report = itinerary_service.generate_travel_report(optimized_itinerary)
        
        return jsonify({
            'success': True,
            'itinerary': travel_report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'行程规划失败: {str(e)}'
        }), 500

@api_bp.route('/weather/predict', methods=['POST'])
def predict_weather():
    """预测未来天气"""
    try:
        import pandas as pd
        from datetime import datetime, timedelta
        
        # 获取请求数据
        data = request.get_json()
        city = data.get('city', '沈阳')
        days = int(data.get('days', 7))
        start_date = data.get('start_date', None)
        
        # 生成模拟天气数据
        predictions = []
        
        # 确定开始日期
        if start_date:
            current_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            current_date = datetime.now()
        
        # 生成未来几天的模拟数据
        for i in range(days):
            date = current_date + timedelta(days=i)
            
            # 生成随机但合理的天气数据
            max_temp = 15 + i % 5 + (i * 0.5)
            min_temp = max_temp - 5 - (i % 3)
            avg_temp = (max_temp + min_temp) / 2
            
            # 计算旅游评分
            if avg_temp >= 15 and avg_temp <= 25:
                travel_score = 90 + (i % 10)
                recommendation = '强烈推荐'
            elif avg_temp >= 10 and avg_temp < 15:
                travel_score = 70 + (i % 10)
                recommendation = '推荐'
            elif avg_temp >= 25 and avg_temp <= 30:
                travel_score = 75 + (i % 10)
                recommendation = '推荐'
            else:
                travel_score = 50 + (i % 10)
                recommendation = '一般'
            
            # 创建预测结果
            prediction = {
                '日期': date.strftime('%Y-%m-%d %H:%M:%S'),
                '最高气温': max_temp,
                '最低气温': min_temp,
                '平均气温': avg_temp,
                '城市': city,
                '旅游评分': int(round(travel_score)),
                '推荐指数': recommendation
            }
            predictions.append(prediction)
        
        return jsonify({
            'success': True,
            'predictions': predictions
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"天气预测详细错误：{error_trace}")
        return jsonify({
            'success': False,
            'message': f'天气预测失败: {str(e)}',
            'trace': error_trace
        }), 500

@api_bp.route('/attractions/list', methods=['GET'])
def list_attractions():
    """获取景点列表"""
    try:
        from app.services.recommendation_service import RecommendationService
        
        # 初始化服务
        data_dir = os.path.abspath(Config.DATA_DIR)
        recommendation_service = RecommendationService(data_dir)
        
        # 获取景点列表
        attractions = recommendation_service.attractions_df.to_dict('records')
        
        return jsonify({
            'success': True,
            'attractions': attractions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取景点列表失败: {str(e)}'
        }), 500

@api_bp.route('/cities/list', methods=['GET'])
def list_cities():
    """获取城市列表"""
    try:
        from app.services.recommendation_service import RecommendationService
        
        # 初始化服务
        data_dir = os.path.abspath(Config.DATA_DIR)
        recommendation_service = RecommendationService(data_dir)
        
        # 获取城市列表
        cities = recommendation_service.get_all_cities()
        
        return jsonify({
            'success': True,
            'cities': cities
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取城市列表失败: {str(e)}'
        }), 500


@api_bp.route('/path/optimize', methods=['POST'])
def optimize_path():
    """生成闭环旅行路径"""
    try:
        # 获取请求数据
        data = request.get_json()
        start_city = data.get('start_city', '沈阳')
        days = int(data.get('days', 3))
        preferences = data.get('preferences', {})
        
        # 初始化服务
        path_service = PathOptimizationService()
        
        # 生成闭环路径
        path_result = path_service.generate_closed_loop_path(
            start_city, days, preferences
        )
        
        # 提取行程和预算
        itinerary = path_result['itinerary']
        budget = path_result['budget']
        
        # 转换为可序列化的格式
        serialized_itinerary = []
        for day_plan in itinerary:
            serialized_day = {
                'day': day_plan['day'],
                'weather': day_plan.get('weather'),
                'adjusted': day_plan.get('adjusted', False),
                'recommended_hotels': day_plan.get('recommended_hotels', []),
                'recommended_dining': day_plan.get('recommended_dining', []),
                'attractions': [
                    {
                        'id': attr.id,
                        'name': attr.name,
                        'city': attr.city,
                        'type': attr.type,
                        'rating': attr.rating,
                        'price': attr.price,
                        'duration': attr.duration,
                        'longitude': attr.longitude,
                        'latitude': attr.latitude,
                        'description': attr.description
                    } for attr in day_plan['attractions']
                ]
            }
            serialized_itinerary.append(serialized_day)
        
        return jsonify({
            'success': True,
            'itinerary': serialized_itinerary,
            'budget': budget
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'路径优化失败: {str(e)}'
        }), 500


@api_bp.route('/path/adjust_for_weather', methods=['POST'])
def adjust_path_for_weather():
    """根据天气调整路径"""
    try:
        # 获取请求数据
        data = request.get_json()
        itinerary = data.get('itinerary')
        weather_forecast = data.get('weather_forecast')
        
        if not itinerary:
            return jsonify({
                'success': False,
                'message': '行程数据不能为空'
            }), 400
        
        if not weather_forecast:
            return jsonify({
                'success': False,
                'message': '天气预报数据不能为空'
            }), 400
        
        # 初始化服务
        path_service = PathOptimizationService()
        
        # 从数据库获取景点对象
        from app.models import Attraction
        
        # 转换行程数据为包含景点对象的格式
        db_itinerary = []
        for day_plan in itinerary:
            # 获取景点对象
            attractions = []
            for attr_data in day_plan['attractions']:
                attr = Attraction.query.get(attr_data['id'])
                if attr:
                    attractions.append(attr)
            
            db_itinerary.append({
                'day': day_plan['day'],
                'attractions': attractions,
                'weather': day_plan.get('weather'),
                'adjusted': day_plan.get('adjusted', False)
            })
        
        # 优化路径
        adjusted_itinerary = path_service.optimize_path_for_weather(
            db_itinerary, weather_forecast
        )
        
        # 转换为可序列化的格式
        serialized_itinerary = []
        for day_plan in adjusted_itinerary:
            serialized_day = {
                'day': day_plan['day'],
                'weather': day_plan.get('weather'),
                'adjusted': day_plan.get('adjusted', False),
                'attractions': [
                    {
                        'id': attr.id,
                        'name': attr.name,
                        'city': attr.city,
                        'type': attr.type,
                        'rating': attr.rating,
                        'price': attr.price,
                        'duration': attr.duration,
                        'longitude': attr.longitude,
                        'latitude': attr.latitude,
                        'description': attr.description
                    } for attr in day_plan['attractions']
                ]
            }
            serialized_itinerary.append(serialized_day)
        
        return jsonify({
            'success': True,
            'adjusted_itinerary': serialized_itinerary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'路径天气调整失败: {str(e)}'
        }), 500


@api_bp.route('/map/generate', methods=['POST'])
def generate_map():
    """生成地图可视化"""
    try:
        # 获取请求数据
        data = request.get_json()
        itinerary = data.get('itinerary')
        
        if not itinerary:
            return jsonify({
                'success': False,
                'message': '行程数据不能为空'
            }), 400
        
        # 从数据库获取景点对象
        from app.models import Attraction
        
        # 转换行程数据为包含景点对象的格式
        db_itinerary = []
        for day_plan in itinerary:
            # 获取景点对象
            attractions = []
            for attr_data in day_plan['attractions']:
                attr = Attraction.query.get(attr_data['id'])
                if attr:
                    attractions.append(attr)
            
            db_itinerary.append({
                'day': day_plan['day'],
                'attractions': attractions,
                'weather': day_plan.get('weather'),
                'adjusted': day_plan.get('adjusted', False)
            })
        
        # 初始化服务
        map_service = MapService()
        
        # 生成地图
        map_object = map_service.generate_travel_map(db_itinerary)
        
        # 返回地图HTML
        return jsonify({
            'success': True,
            'map_html': map_object._repr_html_()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'地图生成失败: {str(e)}'
        }), 500
