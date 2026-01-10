from app import create_app, db
from app.models import Attraction

# 创建应用实例并推入应用上下文
app = create_app()
with app.app_context():
    # 检查数据库连接
    print('检查数据库连接...')
    print(f'数据库URL: {db.engine.url}')

    # 检查Attraction表中的数据
    print('\n检查Attraction表中的数据...')
    attractions = Attraction.query.all()
    print(f'总景点数量: {len(attractions)}')

    # 按城市分组统计
    print('\n按城市分组统计景点数量:')
    city_counts = {}
    for attr in attractions:
        if attr.city in city_counts:
            city_counts[attr.city] += 1
        else:
            city_counts[attr.city] = 1

    for city, count in sorted(city_counts.items()):
        print(f'{city}: {count}个景点')

    # 检查大连的景点
    print('\n检查大连的景点:')
    dalian_attrs = Attraction.query.filter(Attraction.city == '大连市').all()
    print(f'大连市景点数量: {len(dalian_attrs)}')

    # 打印前5个大连景点的详细信息
    print('\n前5个大连景点的详细信息:')
    for attr in dalian_attrs[:5]:
        print(f'ID: {attr.id}, 名称: {attr.name}, 类型: {attr.type}, 评分: {attr.rating}, 价格: {attr.price}, 经纬度: {attr.latitude}, {attr.longitude}')
