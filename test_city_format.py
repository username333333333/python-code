from app import create_app, db
from app.models import Attraction

# 创建应用上下文
app = create_app()
with app.app_context():
    # 查看营口市的景点
    print("营口市的景点:")
    yingkou_attractions = Attraction.query.filter(
        Attraction.city.in_(['营口', '营口市'])
    ).limit(10).all()
    
    for attr in yingkou_attractions:
        print(f"- {attr.name} ({attr.city})")
    
    # 查看所有城市的名称
    print("\n数据库中的城市名称:")
    cities = db.session.query(Attraction.city).distinct().all()
    for city in cities:
        print(f"- {city[0]}")