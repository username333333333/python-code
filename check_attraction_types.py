from app import create_app
from app.models import Attraction, db

# 创建Flask应用上下文
app = create_app()
with app.app_context():
    # 获取所有景点的类型
    attractions = Attraction.query.all()
    types = set()
    
    for attraction in attractions:
        if attraction.type:
            types.add(attraction.type)
    
    print(f'共有 {len(types)} 种不同的景点类型')
    print('\n所有景点类型:')
    for t in sorted(types):
        print(f'  - {t}')
    
    # 检查特定类型的景点数量
    print('\n各类型景点数量:')
    for t in sorted(types):
        count = Attraction.query.filter(Attraction.type == t).count()
        print(f'  {t}: {count} 个')
    
    # 检查沈阳和营口的景点
    print('\n沈阳的景点数量:', Attraction.query.filter(Attraction.city == '沈阳').count())
    print('营口的景点数量:', Attraction.query.filter(Attraction.city == '营口').count())
    
    # 检查符合用户偏好的景点数量
    user_types = ['博物馆', '公园', '风景区']
    print(f'\n符合用户偏好类型的景点数量:')
    for t in user_types:
        count = Attraction.query.filter(Attraction.type.like(f'%{t}%')).count()
        print(f'  {t}: {count} 个')
    
    # 查看前5个沈阳的景点
    print('\n沈阳前5个景点:')
    shenyang_attractions = Attraction.query.filter(Attraction.city == '沈阳').limit(5).all()
    for a in shenyang_attractions:
        print(f'  {a.name} - 类型: {a.type}')
    
    # 查看前5个营口的景点
    print('\n营口前5个景点:')
    yingkou_attractions = Attraction.query.filter(Attraction.city == '营口').limit(5).all()
    for a in yingkou_attractions:
        print(f'  {a.name} - 类型: {a.type}')
