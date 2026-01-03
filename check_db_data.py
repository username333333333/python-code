from app import create_app
from app.models import Attraction, TrafficRecord, RiskAssessment

app = create_app()

with app.app_context():
    # 检查景点数据
    attraction_count = Attraction.query.count()
    print(f"数据库中景点数量: {attraction_count}")
    print("\n前5个景点示例:")
    for attr in Attraction.query.limit(5).all():
        print(f"{attr.id}: {attr.name} - {attr.city}")
    
    # 检查客流量数据
    traffic_count = TrafficRecord.query.count()
    print(f"\n数据库中客流量记录数量: {traffic_count}")
    print("\n前5个客流量记录示例:")
    for traffic in TrafficRecord.query.limit(5).all():
        print(f"{traffic.id}: {traffic.attraction.name} - {traffic.date} - {traffic.traffic}人")
    
    # 检查风险评估数据
    risk_count = RiskAssessment.query.count()
    print(f"\n数据库中风险评估记录数量: {risk_count}")
    print("\n前5个风险评估记录示例:")
    for risk in RiskAssessment.query.limit(5).all():
        print(f"{risk.id}: {risk.attraction.name} - {risk.risk_level}风险")
