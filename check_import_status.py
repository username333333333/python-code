from app import create_app
from app.models import Attraction, TrafficRecord, RiskAssessment

app = create_app()

with app.app_context():
    print("当前数据库数据统计：")
    print(f"景点数量: {Attraction.query.count()}")
    print(f"客流量记录: {TrafficRecord.query.count()}")
    print(f"风险评估记录: {RiskAssessment.query.count()}")
