from app.models import Attraction
from app import db

# 创建应用上下文
from app import create_app
app = create_app()
with app.app_context():
    # 获取所有景点
    attractions = Attraction.query.all()
    print(f'总景点数: {len(attractions)}')
    
    # 统计有效坐标的景点
    valid_coords = [a for a in attractions if a.latitude and a.longitude]
    print(f'有效坐标景点数: {len(valid_coords)}')
    
    # 查看前5个有效坐标景点
    print('前5个有效坐标景点:')
    for a in valid_coords[:5]:
        print(f'  {a.name} ({a.city}): ({a.latitude}, {a.longitude})')
    
    # 查看沈阳和营口的景点
    print('\n沈阳的景点:')
    shenyang_attractions = [a for a in attractions if a.city == '沈阳']
    for a in shenyang_attractions[:5]:
        print(f'  {a.name}: 坐标 ({a.latitude}, {a.longitude})')
    
    print('\n营口的景点:')
    yingkou_attractions = [a for a in attractions if a.city == '营口']
    for a in yingkou_attractions[:5]:
        print(f'  {a.name}: 坐标 ({a.latitude}, {a.longitude})')
