from app.services.path_optimization_service import PathOptimizationService

# 初始化服务
path_service = PathOptimizationService()

# 测试案例：起点营口，终点沈阳
try:
    print("测试案例：起点营口，终点沈阳")
    itinerary = path_service.generate_closed_loop_path('营口', 3, {}, '沈阳', [])
    print('行程生成完成')
    
    for day_plan in itinerary:
        print(f'第{day_plan["day"]}天')
        for attr_info in day_plan['attractions']:
            attr = attr_info['attraction']
            print(f'  - {attr.name} ({attr.city})')
    
    print("\n测试案例：起点沈阳，终点沈阳")
    itinerary = path_service.generate_closed_loop_path('沈阳', 3, {}, '沈阳', [])
    print('行程生成完成')
    
    for day_plan in itinerary:
        print(f'第{day_plan["day"]}天')
        for attr_info in day_plan['attractions']:
            attr = attr_info['attraction']
            print(f'  - {attr.name} ({attr.city})')
    
except Exception as e:
    print(f'测试失败：{str(e)}')
    import traceback
    traceback.print_exc()