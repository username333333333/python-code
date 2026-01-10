from app import create_app
from app.models import Attraction

app = create_app()

with app.app_context():
    # 连接到数据库
    from app import db
    
    print("检查数据库中的城市格式...")
    
    # 查询前10个景点的城市字段
    attractions = Attraction.query.limit(10).all()
    
    print("\n前10个景点的城市字段:")
    for attr in attractions:
        print(f"景点: {attr.name}, 城市: '{attr.city}'")
    
    # 统计所有城市及其出现次数
    print("\n所有城市及其出现次数:")
    cities = db.session.query(Attraction.city, db.func.count(Attraction.id)).group_by(Attraction.city).all()
    for city, count in sorted(cities, key=lambda x: x[1], reverse=True):
        print(f"'{city}': {count}个景点")
    
    # 检查大连的景点数量
    print("\n检查大连的景点数量:")
    # 查询不带"市"后缀的大连
    dalian_attrs = Attraction.query.filter(Attraction.city == '大连').all()
    print(f"'大连'景点数量: {len(dalian_attrs)}")
    
    # 查询带"市"后缀的大连
    dalian_attrs_with_suffix = Attraction.query.filter(Attraction.city == '大连市').all()
    print(f"'大连市'景点数量: {len(dalian_attrs_with_suffix)}")
