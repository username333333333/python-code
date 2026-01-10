from app import create_app
from app.services.path_optimization_service import PathOptimizationService
from app.services.recommendation_service import RecommendationService
import os
from app.config import Config

app = create_app()

# 测试行程规划功能
with app.app_context():
    try:
        print("=== 测试行程规划功能 ===")
        
        # 初始化路径优化服务
        path_service = PathOptimizationService()
        print("路径优化服务初始化成功")
        
        # 初始化推荐服务，用于获取城市和景点数据
        data_dir = os.path.abspath(Config.DATA_DIR)
        recommendation_service = RecommendationService(data_dir)
        print("推荐服务初始化成功")
        
        # 测试获取所有城市
        cities = recommendation_service.get_all_cities()
        print(f"获取城市列表成功，共 {len(cities)} 个城市")
        print(f"城市列表: {cities}")
        
        # 选择测试城市和景点
        test_city = "沈阳"
        
        # 测试生成闭环路径
        print(f"\n测试为 {test_city} 生成闭环路径...")
        
        # 准备行程数据
        itinerary_data = {
            'start_city': test_city,
            'target_city': test_city,
            'days': 2,
            'selected_attractions': [],  # 不使用用户选择的景点，让系统自动推荐
            'preferences': {
                'attraction_types': ['风景名胜'],
                'min_rating': 4.0
            }
        }
        
        # 调用路径优化服务生成行程
        itinerary_result = path_service.generate_closed_loop_path(
            start_city=test_city,
            days=2,
            preferences=itinerary_data['preferences'],
            target_city=test_city,
            selected_attractions=[]  # 不使用用户选择的景点
        )
        
        if itinerary_result and 'itinerary' in itinerary_result:
            print("\n行程生成成功!")
            print(f"总天数: {len(itinerary_result['itinerary'])}")
            
            # 打印每天的行程
            for day_idx, day_plan in enumerate(itinerary_result['itinerary']):
                print(f"\n第 {day_idx + 1} 天行程:")
                for attraction_info in day_plan['attractions']:
                    if isinstance(attraction_info, dict) and 'attraction' in attraction_info:
                        attr = attraction_info['attraction']
                        print(f"  - {attr.name} ({attr.type}) - 评分: {attr.rating} - 门票: {attr.price}元")
                    else:
                        print(f"  - {attraction_info.name} ({attraction_info.type}) - 评分: {attraction_info.rating} - 门票: {attraction_info.price}元")
                
            # 打印预算信息
            if 'budget' in itinerary_result:
                print(f"\n预算信息:")
                print(f"总费用: {itinerary_result['budget'].get('total_cost', 0)} 元")
                
                # 打印交通费用
                if 'transportation' in itinerary_result['budget']:
                    print(f"交通费用: {itinerary_result['budget']['transportation']} 元")
                
                # 打印门票费用
                if 'tickets' in itinerary_result['budget']:
                    print(f"门票费用: {itinerary_result['budget']['tickets']} 元")
            
            print("\n行程规划功能测试通过!")
        else:
            print(f"行程生成失败: 无法获取行程信息")
        
    except Exception as e:
        print(f"\n=== 行程规划功能测试失败: {str(e)} ===")
        import traceback
        traceback.print_exc()
