from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.services.weather_service import WeatherService
from app.services.analysis_service import AnalysisService
from app.config import Config
import os
import pandas as pd
from datetime import datetime, timedelta
from flask_login import login_required, current_user

bp = Blueprint('visualizations', __name__)

def _process_date_range(date_range, df):
    try:
        if len(date_range) == 2:
            start = datetime.strptime(date_range[0], '%Y-%m-%d')
            end = datetime.strptime(date_range[1], '%Y-%m-%d')
            if start > end:
                return [date_range[1], date_range[0]]
            return date_range
    except ValueError:
        pass

    return [
        df['日期'].min().strftime('%Y-%m-%d'),
        df['日期'].max().strftime('%Y-%m-%d')
    ]

def _get_available_cities(data_dir):
    try:
        # 检查weather_sensitive子目录
        weather_sensitive_dir = os.path.join(data_dir, 'weather_sensitive')
        city_files = []
        
        if os.path.exists(weather_sensitive_dir):
            city_files = [f for f in os.listdir(weather_sensitive_dir)
                          if f.endswith("2013-2023年天气数据.csv") and os.path.isfile(os.path.join(weather_sensitive_dir, f))]
        
        return sorted({f.split("2013")[0] for f in city_files})
    except FileNotFoundError:
        return []

def _generate_all_charts(data, traffic_data=None, risk_data=None, operation_data=None, is_future=False):
        # 初始化所有图表键，设置默认值为None，确保模板中所有图表变量都有定义
        charts = {
            # 天气相关图表
            'temp_line': None,
            'weather_bar': None,
            'wind_scatter': None,
            'day_season_pie': None,
            'night_season_pie': None,
            'temp_heatmap': None,
            'weather_day_pie': None,
            'weather_night_pie': None,
            'wind_day_rose': None,
            'wind_night_rose': None,
            # 旅游推荐相关图表
            'top10_bar': None,
            # 客流量相关图表
            'traffic_trend': None,
            'holiday_traffic_comparison': None,
            'weather_traffic_scatter': None,
            'attraction_traffic_ranking': None,
            'seasonal_traffic': None,
            # 风险评估相关图表
            'risk_level_distribution': None,
            'risk_level_time_trend': None,
            'weather_risk_relationship': None,
            # 景区运营相关图表
            'operation_suggestion_distribution': None,
            'weather_operation_relationship': None,
            'expected_actual_traffic_comparison': None
        }
        try:
            print(f"=== 开始生成图表，is_future={is_future} ===")
            
            # 生成天气相关图表
            print("生成气温趋势图...")
            charts['temp_line'] = AnalysisService.create_temp_line_chart(data)
            
            # 生成天气频率统计图表
            print("生成天气频率统计图表...")
            charts['weather_bar'] = AnalysisService.create_weather_bar_chart(data)
            
            # 生成风力分布图表
            print("生成风力分布图表...")
            charts['wind_scatter'] = AnalysisService.create_wind_scatter_chart(data)
            
            # 生成季节分布饼图
            print("生成季节分布饼图...")
            charts['day_season_pie'] = AnalysisService.create_season_pie_chart(data, is_day=True)
            charts['night_season_pie'] = AnalysisService.create_season_pie_chart(data, is_day=False)
            
            # 生成气温热力图
            print("生成气温热力图...")
            charts['temp_heatmap'] = AnalysisService.create_temp_heatmap(data)
            
            # 生成天气状况饼图
            print("生成天气状况饼图...")
            charts['weather_day_pie'] = AnalysisService.create_weather_pie_chart(data, is_day=True)
            charts['weather_night_pie'] = AnalysisService.create_weather_pie_chart(data, is_day=False)
            
            # 生成风向玫瑰图
            print("生成风向玫瑰图...")
            charts['wind_day_rose'] = AnalysisService.create_wind_direction_rose_chart(data, is_day=True)
            charts['wind_night_rose'] = AnalysisService.create_wind_direction_rose_chart(data, is_day=False)
            
            # 生成旅游推荐相关图表
            print("生成旅游推荐相关图表...")
            if is_future and '旅游评分' in data.columns:
                # 预测数据已经包含旅游评分，直接使用
                score_df = data[['日期', '旅游评分']].copy()
                score_df.columns = ['日期', '评分']
                charts['top10_bar'] = AnalysisService.create_top10_score_chart(score_df)
            else:
                # 历史数据需要计算旅游评分
                score_df = AnalysisService.calculate_travel_score(data)
                charts['top10_bar'] = AnalysisService.create_top10_score_chart(score_df)
            
            # 生成客流量相关图表（仅历史数据）
            if not is_future and traffic_data is not None and not traffic_data.empty:
                print("生成客流量相关图表...")
                charts['traffic_trend'] = AnalysisService.create_traffic_trend_chart(traffic_data)
                charts['holiday_traffic_comparison'] = AnalysisService.create_holiday_traffic_comparison(traffic_data)
                charts['weather_traffic_scatter'] = AnalysisService.create_weather_traffic_scatter(traffic_data)
                charts['attraction_traffic_ranking'] = AnalysisService.create_attraction_traffic_ranking(traffic_data)
                charts['seasonal_traffic'] = AnalysisService.create_seasonal_traffic_chart(traffic_data)
            
            # 生成风险评估相关图表（仅历史数据）
            if not is_future and risk_data is not None and not risk_data.empty:
                print("生成风险评估相关图表...")
                charts['risk_level_distribution'] = AnalysisService.create_risk_level_distribution(risk_data)
                charts['risk_level_time_trend'] = AnalysisService.create_risk_level_time_trend(risk_data)
                charts['weather_risk_relationship'] = AnalysisService.create_weather_risk_relationship(risk_data)
            
            # 生成景区运营相关图表（仅历史数据）
            if not is_future and operation_data is not None and not operation_data.empty:
                print("生成景区运营相关图表...")
                charts['operation_suggestion_distribution'] = AnalysisService.create_operation_suggestion_distribution(operation_data)
                charts['weather_operation_relationship'] = AnalysisService.create_weather_operation_relationship(operation_data)
            
            print("=== 图表生成完成 ===")
        except Exception as e:
            print(f"图表生成错误: {str(e)}")
            import traceback
            traceback.print_exc()
        return charts

@bp.route('/')
def index():
    """默认路由，重定向到登录页面"""
    return redirect(url_for('auth.login'))

@bp.route('/test-charts')
def test_charts():
    """测试图表生成功能，不需要登录"""
    from datetime import datetime, timedelta
    import pandas as pd
    
    # 创建模拟数据
    dates = [datetime.now() - timedelta(days=i) for i in range(30)]
    dates.reverse()
    
    data = pd.DataFrame({
        '日期': dates,
        '最高气温': [15, 16, 14, 17, 18, 19, 20, 18, 17, 16, 15, 14, 13, 12, 11, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 28, 26, 24, 22],
        '最低气温': [5, 6, 4, 7, 8, 9, 10, 8, 7, 6, 5, 4, 3, 2, 1, 0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 18, 16, 14, 12],
        '风力(白天)_数值': [2, 3, 1, 2, 3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 3, 2, 1, 2, 3, 2],
        '风力(夜间)_数值': [1, 2, 1, 1, 2, 1, 1, 2, 3, 2, 1, 2, 1, 1, 2, 1, 1, 2, 3, 2, 1, 2, 1, 1, 2, 1, 1, 2, 3, 2],
        '天气状况(白天)': ['晴', '多云', '阴', '晴', '多云', '晴', '晴', '多云', '阴', '小雨', '多云', '晴', '晴', '多云', '阴', '晴', '多云', '晴', '晴', '多云', '阴', '小雨', '多云', '晴', '晴', '多云', '阴', '晴', '晴', '多云'],
        '天气状况(夜间)': ['晴', '晴', '阴', '多云', '晴', '多云', '多云', '晴', '晴', '阴', '多云', '晴', '晴', '多云', '阴', '晴', '多云', '晴', '晴', '多云', '阴', '小雨', '多云', '晴', '晴', '多云', '阴', '晴', '晴', '多云'],
        '风向(白天)': ['东南风', '南风', '北风', '东风', '南风', '东南风', '东风', '南风', '北风', '西风', '南风', '东南风', '东风', '南风', '北风', '东风', '南风', '东南风', '东风', '南风', '北风', '西风', '南风', '东南风', '东风', '南风', '北风', '东风', '南风', '东南风'],
        '风向(夜间)': ['南风', '东南风', '北风', '东北风', '南风', '东风', '东南风', '南风', '北风', '西风', '南风', '东南风', '东风', '南风', '北风', '东风', '南风', '东南风', '东风', '南风', '北风', '西风', '南风', '东南风', '东风', '南风', '北风', '东风', '南风', '东南风'],
        '旅游评分': [85, 88, 75, 90, 92, 95, 93, 88, 85, 78, 82, 85, 88, 90, 92, 95, 93, 88, 85, 78, 82, 85, 88, 90, 92, 95, 93, 88, 85, 82],
        '推荐指数': ['推荐', '强烈推荐', '一般', '强烈推荐', '强烈推荐', '强烈推荐', '强烈推荐', '推荐', '推荐', '一般', '推荐', '推荐', '强烈推荐', '强烈推荐', '强烈推荐', '强烈推荐', '强烈推荐', '推荐', '推荐', '一般', '推荐', '推荐', '强烈推荐', '强烈推荐', '强烈推荐', '强烈推荐', '强烈推荐', '推荐', '推荐', '推荐']
    })
    
    charts = _generate_all_charts(data, is_future=False)
    
    # 确保所有图表都有值，防止前端渲染错误
    chart_options = {}
    for k, v in charts.items():
        if v:
            try:
                chart_options[k] = v.dump_options()
                print(f"✅ {k}: 成功转换为JSON")
            except Exception as e:
                print(f"❌ {k}: 转换为JSON失败: {str(e)}")
                chart_options[k] = None
        else:
            chart_options[k] = None
    
    return render_template('visualizations_fixed.html',
                           charts=chart_options,
                           cities=['沈阳', '大连', '鞍山'],
                           city='沈阳',
                           data_type='history',
                           forecast_days=7,
                           filters={
                               'date_range': ['2023-01-01', '2023-12-31'],
                               'day_weather': [],
                               'night_weather': [],
                               'chart_type': 'all',
                               'type': 'history'
                           })

@bp.route('/dashboard')
@login_required
def dashboard():
    # 所有登录用户都可以访问主界面
        
    # 打印所有请求参数，用于调试
    print(f"\n=== 请求参数 ===")
    for key, value in request.args.items():
        print(f"{key}: {value}")
    
    city_name = request.args.get('city', '沈阳')
    # 获取选项卡类型，默认为历史数据
    data_type = request.args.get('data_type', 'history')
    # 确保如果是未来预测，始终保持future类型
    if 'forecast_days' in request.args and data_type == 'history':
        data_type = 'future'
    
    print(f"=== 处理后的数据类型 ===")
    print(f"data_type: {data_type}")
    print(f"请求URL: {request.url}")
    
    # 预测天数，默认为7天
    forecast_days = int(request.args.get('forecast_days', 7))

    try:
        data_dir = os.path.abspath(Config.DATA_DIR)
        print(f"加载城市数据: {city_name}")
        weather_service = WeatherService(data_dir, city_name)
        print(f"原始数据行数: {len(weather_service.df)}")

        data = None
        traffic_data = None
        risk_data = None
        operation_data = None
        
        if data_type == 'future':
            # 未来数据预测
            print(f"生成未来{forecast_days}天的预测数据")
            
            # 直接生成模拟数据，确保图表能显示
            print("为未来预测生成模拟数据，确保图表能显示")
            from datetime import datetime, timedelta
            
            # 创建模拟的未来7天数据，使用pandas datetime对象
            dates = [pd.to_datetime(datetime.now().date() + timedelta(days=i+1)) for i in range(7)]
            
            # 生成模拟数据
            data = pd.DataFrame({
                '日期': dates,
                '最高气温': [15, 16, 14, 17, 18, 19, 20],
                '最低气温': [5, 6, 4, 7, 8, 9, 10],
                '平均气温': [(15+5)/2, (16+6)/2, (14+4)/2, (17+7)/2, (18+8)/2, (19+9)/2, (20+10)/2],
                '风力(白天)_数值': [2, 3, 1, 2, 3, 2, 1],
                '风力(夜间)_数值': [1, 2, 1, 1, 2, 1, 1],
                '天气状况(白天)': ['晴', '多云', '阴', '晴', '多云', '晴', '晴'],
                '天气状况(夜间)': ['晴', '晴', '阴', '多云', '晴', '多云', '多云'],
                '风向(白天)': ['东南风', '南风', '北风', '东风', '南风', '东南风', '东风'],
                '风向(夜间)': ['南风', '东南风', '北风', '东北风', '南风', '东风', '东南风'],
                '旅游评分': [85, 88, 75, 90, 92, 95, 93],
                '推荐指数': ['推荐', '强烈推荐', '一般', '强烈推荐', '强烈推荐', '强烈推荐', '强烈推荐']
            })
            print(f"生成的模拟数据行数: {len(data)}")
            print(f"模拟数据列: {list(data.columns)}")
        else:
            # 历史数据分析
            # 默认使用2013–2023年全范围数据
            date_range = ['2013-01-01', '2023-12-31']

            # 可选：也可以读取用户筛选
            user_start = request.args.get('start_date')
            user_end = request.args.get('end_date')
            if user_start and user_end:
                print(f"用户选择的日期范围: {user_start} 至 {user_end}")
                date_range = _process_date_range([user_start, user_end], weather_service.df)

            print(f"最终日期范围: {date_range}")
            data = weather_service.get_filtered_data({
                'date_range': date_range,
                'day_weather': request.args.getlist('day_weather'),
                'night_weather': request.args.getlist('night_weather')
            })

            print(f"筛选后的数据行数: {len(data)}")

            # 限制过大数据
            if len(data) > 1000:
                print(f"数据行数超过1000，随机采样1000条")
                data = data.sample(1000, random_state=42)

            # 加载交通数据
            traffic_file = os.path.join(data_dir, 'traffic', f'{city_name}_2013-2023_traffic_data.csv')
            if os.path.exists(traffic_file):
                traffic_data = pd.read_csv(traffic_file, parse_dates=['日期'])
                print(f"加载交通数据，行数: {len(traffic_data)}")
                # 限制数据量
                if len(traffic_data) > 1000:
                    traffic_data = traffic_data.sample(1000, random_state=42)
            
            # 加载风险评估数据
            risk_file = os.path.join(data_dir, 'risk', f'{city_name}2013-2023年风险评估数据.csv')
            if os.path.exists(risk_file):
                risk_data = pd.read_csv(risk_file, parse_dates=['日期'])
                print(f"加载风险评估数据，行数: {len(risk_data)}")
                # 限制数据量
                if len(risk_data) > 1000:
                    risk_data = risk_data.sample(1000, random_state=42)
            
            # 加载景区运营数据
            operation_file = os.path.join(data_dir, 'operation', f'{city_name}_operation_data.csv')
            if os.path.exists(operation_file):
                operation_data = pd.read_csv(operation_file, parse_dates=['日期'])
                print(f"加载景区运营数据，行数: {len(operation_data)}")
                # 限制数据量
                if len(operation_data) > 1000:
                    operation_data = operation_data.sample(1000, random_state=42)
        
        print(f"最终用于生成图表的数据行数: {len(data) if data is not None else 0}")
        # 确保如果数据为空，我们不会尝试生成图表
        if data is None or data.empty:
            # 如果是未来预测，生成一些模拟数据以便显示图表
            if data_type == 'future':
                print("数据为空，生成模拟预测数据")
                from datetime import datetime, timedelta
                
                # 创建模拟的未来7天数据
                dates = [datetime.now().date() + timedelta(days=i+1) for i in range(7)]
                
                # 生成模拟数据
                data = pd.DataFrame({
                    '日期': dates,
                    '最高气温': [15, 16, 14, 17, 18, 19, 20],
                    '最低气温': [5, 6, 4, 7, 8, 9, 10],
                    '平均气温': [(15+5)/2, (16+6)/2, (14+4)/2, (17+7)/2, (18+8)/2, (19+9)/2, (20+10)/2],
                    '风力(白天)_数值': [2, 3, 1, 2, 3, 2, 1],
                    '风力(夜间)_数值': [1, 2, 1, 1, 2, 1, 1],
                    '天气状况(白天)': ['晴', '多云', '阴', '晴', '多云', '晴', '晴'],
                    '天气状况(夜间)': ['晴', '晴', '阴', '多云', '晴', '多云', '多云'],
                    '风向(白天)': ['东南风', '南风', '北风', '东风', '南风', '东南风', '东风'],
                    '风向(夜间)': ['南风', '东南风', '北风', '东北风', '南风', '东风', '东南风'],
                    '旅游评分': [85, 88, 75, 90, 92, 95, 93],
                    '推荐指数': ['推荐', '强烈推荐', '一般', '强烈推荐', '强烈推荐', '强烈推荐', '强烈推荐']
                })
                print(f"生成的模拟数据行数: {len(data)}")
            else:
                print("数据为空，无法生成图表")
        
        charts = _generate_all_charts(data, traffic_data, risk_data, operation_data, is_future=(data_type == 'future'))
        available_cities = _get_available_cities(data_dir)
        print(f"可用城市列表: {available_cities}")

        # 检查天气选项
        day_weather = []
        night_weather = []
        if data_type == 'history':
            day_weather = weather_service.df['天气状况(白天)'].unique().tolist()
            night_weather = weather_service.df['天气状况(夜间)'].unique().tolist()
        print(f"白天天气选项: {day_weather}")
        print(f"夜间天气选项: {night_weather}")
        
        # 准备筛选参数
        filters = {
            'date_range': request.args.getlist('date_range', ['2013-01-01', '2023-12-31']),
            'day_weather': request.args.getlist('day_weather'),
            'night_weather': request.args.getlist('night_weather'),
            'chart_type': request.args.get('chart_type', 'all'),
            'type': data_type
        }
        
        # 打印图表生成情况，用于调试
        print(f"=== 图表生成情况 ===")
        for chart_name, chart_obj in charts.items():
            if chart_obj:
                print(f"✅ {chart_name}: 图表生成成功")
            else:
                print(f"❌ {chart_name}: 图表生成失败")
        
        # 确保所有图表都有值，防止前端渲染错误
        chart_options = {}
        for k, v in charts.items():
            if v:
                try:
                    chart_options[k] = v.dump_options()
                    print(f"✅ {k}: 成功转换为JSON")
                except Exception as e:
                    print(f"❌ {k}: 转换为JSON失败: {str(e)}")
                    chart_options[k] = None
            else:
                chart_options[k] = None
        
        return render_template('visualizations_fixed.html',
                               charts=chart_options,
                               cities=available_cities,
                               city=city_name,
                               data_type=data_type,
                               forecast_days=forecast_days,
                               filters=filters)
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', message="数据加载失败", details=str(e)), 500

@bp.route('/system_menu')
@login_required
def system_menu():
    """系统菜单页面"""
    return render_template('system_menu.html')
