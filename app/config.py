import os
from pathlib import Path


class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'

    # 项目根目录（根据实际项目结构调整）
    BASE_DIR = Path(__file__).parent.parent  # 假设config.py在app目录下

    # 数据目录配置
    DATA_DIR = BASE_DIR / 'data'  # 数据目录在项目根目录下

    # 检查数据目录是否存在
    if not DATA_DIR.exists():
        raise RuntimeError(f"数据目录不存在: {DATA_DIR}")
    
    # 检查是否有天气数据文件
    weather_data_files = list(DATA_DIR.glob('**/*天气数据.csv'))  # 递归查找所有子目录
    if not weather_data_files:
        raise RuntimeError(f"数据目录中没有找到天气数据文件: {DATA_DIR}")
    
    # 数据库配置 - SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 日志配置
    LOG_DIR = BASE_DIR / 'logs'
    LOG_FILE = LOG_DIR / 'app.log'
    
    # 预测服务配置
    PREDICTION_SERVICE_TYPE = os.environ.get('PREDICTION_SERVICE_TYPE') or 'sklearn'  # sklearn or spark

    @classmethod
    def create_dirs(cls):
        """创建必要的目录结构"""
        os.makedirs(cls.LOG_DIR, exist_ok=True)
