from flask import Blueprint, render_template
from app.services.weather_service import WeatherService

bp = Blueprint('dashboard', __name__)

@bp.route('/')
def index():
    from app.config import Config
    default_city = '沈阳'
    data_dir = os.path.abspath(Config.DATA_DIR)
    try:
        # 初始化WeatherService实例
        weather_service = WeatherService(data_dir, default_city)
        weather_data = weather_service.df
        # 计算旅游评分并获取前10天
        top_days = weather_data.nlargest(10, '旅游评分')
        return render_template('dashboard.html',
                             weather_data=weather_data,
                             top_days=top_days)
    except Exception as e:
        return render_template('error.html', message="数据加载失败", details=str(e))