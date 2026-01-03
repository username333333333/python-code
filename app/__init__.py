from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

# 初始化数据库
db = SQLAlchemy()

# 创建日志目录
Config.create_dirs()

# 导入模型，确保数据库表能被创建
from app import models

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 配置日志记录
    if not app.debug and not app.testing:
        # 设置日志级别
        app.logger.setLevel(logging.INFO)
        
        # 创建RotatingFileHandler，限制日志文件大小为10MB，保留5个备份
        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # 添加日志处理器
        app.logger.addHandler(file_handler)
        app.logger.info('Application startup')
    
    # 初始化数据库
    db.init_app(app)
    
    # 导入并注册蓝图
    from app.routes.visualizations import bp as visualizations_bp
    from app.routes.map_view import bp as map_view_bp
    from app.routes.query_view import query_view as query_bp
    from app.routes.recommendation_view import recommendation_view as recommendation_bp
    from app.routes.prediction_view import prediction_view as prediction_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.log_view import log_view as log_bp
    from app.routes.user_management import user_management as user_management_bp
    from app.routes.user_profile import user_profile as user_profile_bp
    from app.routes.api import api_bp as api_bp
    from app.routes.path_optimization import path_bp as path_optimization_bp
    from app.routes.tourism_decision_center import tourism_decision_center as tourism_decision_center_bp

    app.register_blueprint(visualizations_bp)
    app.register_blueprint(map_view_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(user_management_bp)
    app.register_blueprint(user_profile_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(path_optimization_bp)
    app.register_blueprint(tourism_decision_center_bp)
    
    # 创建数据库表（如果不存在）
    with app.app_context():
        db.create_all()
        
        # 预加载和缓存数据，优化应用性能
    # 只在首次启动时执行预加载，避免调试模式重启时重复执行
    if not hasattr(app, '_preloaded'):
        print("开始预加载和缓存数据...")
        import sys
        import os
        
        # 将项目根目录添加到Python路径
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        try:
            from scripts.optimize_loading import optimize_data_loader, optimize_prediction_models, optimize_recommendation_service
            
            # 预加载所有城市数据
            optimize_data_loader()
            
            # 预训练所有城市的预测模型
            optimize_prediction_models()
            
            # 预加载推荐服务数据
            optimize_recommendation_service()
            
            print("数据预加载和缓存完成！")
            # 标记为已预加载
            app._preloaded = True
        except Exception as e:
            print(f"数据预加载和缓存过程中出现错误: {e}")
            import traceback
            traceback.print_exc()

    return app
