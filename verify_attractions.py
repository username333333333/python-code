from app import create_app
from app.models import Attraction, db

# 创建Flask应用上下文
app = create_app()
with app.app_context():
    # 获取所有景点
    attractions = Attraction.query.all()
    print(f'总景点数: {len(attractions)}')
    
    # 统计有效坐标的景点
    valid_coords = [a for a in attractions if a.latitude and a.longitude]
    print(f'有效坐标景点数: {len(valid_coords)}')
    print(f'有效坐标比例: {len(valid_coords)/len(attractions)*100:.2f}%')
    
    # 查看前5个有效坐标景点
    print('\n前5个有效坐标景点:')
    for a in valid_coords[:5]:
        print(f'  {a.name} ({a.city}): ({a.latitude}, {a.longitude})')
    
    # 查看沈阳和营口的景点
    print('\n沈阳的有效坐标景点:')
    shenyang_attractions = [a for a in valid_coords if a.city == '沈阳']
    for a in shenyang_attractions[:3]:
        print(f'  {a.name}: ({a.latitude}, {a.longitude})')
    
    print('\n营口的有效坐标景点:')
    yingkou_attractions = [a for a in valid_coords if a.city == '营口']
    for a in yingkou_attractions[:3]:
        print(f'  {a.name}: ({a.latitude}, {a.longitude})')
