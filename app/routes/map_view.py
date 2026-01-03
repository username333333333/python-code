from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.services.weather_service import WeatherService
from app.services.analysis_service import AnalysisService
from app.services.prediction_service import WeatherPredictionServiceFactory
from app.utils.data_loader import load_all_city_data
from app.config import Config
import os
from datetime import datetime
import pandas as pd
from flask_login import login_required, current_user

bp = Blueprint('map_view', __name__, url_prefix='/map')


@bp.route('/')
@login_required
def index():
        
    try:
        data_dir = os.path.abspath(Config.DATA_DIR)
        
        # 获取选项卡类型，默认为历史地图
        map_type = request.args.get('type', 'history')
        
        # 默认值
        user_start = "2013-01-01"
        user_end = "2023-12-31"
        days = 7
        charts = {}
        
        # 无论是否有days参数，都根据map_type生成对应的地图
        if map_type == 'future':
            # 未来天气地图可视化
            # 从请求中获取天数，默认为7天
            days = int(request.args.get('days', 7))
            
            # 加载所有天气数据
            weather_df = load_all_city_data()
            
            # 初始化预测服务
            from app.services.prediction_service import WeatherPredictionServiceFactory
            prediction_service = WeatherPredictionServiceFactory.create_service(service_type="sklearn", data_dir=data_dir)
            
            # 预测所有城市的未来天气
            all_predictions = prediction_service.predict_all_cities(weather_df, days=days)
            
            # 合并所有城市的预测结果
            future_df_list = []
            for city, df in all_predictions.items():
                if not df.empty:
                    future_df_list.append(df)
            
            if future_df_list:
                future_df = pd.concat(future_df_list, ignore_index=True)
                
                # 创建未来天气地图
                charts['map_future_temp'] = AnalysisService.create_liaoning_temp_map(future_df).dump_options_with_quotes()
                charts['map_future_wind'] = AnalysisService.create_liaoning_wind_map(future_df).dump_options_with_quotes()
        else:
            # 历史地图可视化
            # 直接使用load_all_city_data函数加载所有城市数据，确保数据加载正确
            full_df = load_all_city_data()
            
            # 如果数据为空，返回错误
            if full_df.empty:
                return render_template("error.html", message="未加载任何城市数据")

            # 默认起止时间范围
            default_start = "2013-01-01"
            default_end = "2023-12-31"
            user_start = request.args.get('start_date', default_start)
            user_end = request.args.get('end_date', default_end)

            try:
                start = pd.to_datetime(user_start)
                end = pd.to_datetime(user_end)
                full_df = full_df[(full_df['日期'] >= start) & (full_df['日期'] <= end)]
            except Exception:
                pass

            # 确保数据不为空再生成地图
            if not full_df.empty:
                charts = {
                    'map_temp': AnalysisService.create_liaoning_temp_map(full_df).dump_options_with_quotes(),
                    'map_wind': AnalysisService.create_liaoning_wind_map(full_df).dump_options_with_quotes(),
                }
            else:
                # 如果过滤后数据为空，使用原始数据生成地图
                charts = {
                    'map_temp': AnalysisService.create_liaoning_temp_map(load_all_city_data()).dump_options_with_quotes(),
                    'map_wind': AnalysisService.create_liaoning_wind_map(load_all_city_data()).dump_options_with_quotes(),
                }

        return render_template("map_visualization.html", 
                               charts=charts,
                               filters={'date_range': [user_start, user_end]},
                               map_type=map_type,
                               days=days)
    except Exception as e:
        return render_template("error.html", message="地图加载失败", details=str(e))
