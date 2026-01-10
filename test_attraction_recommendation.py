from app import create_app
from app.services.recommendation_service import RecommendationService
from app.utils.data_loader import load_all_city_data
import os
from app.config import Config

app = create_app()

# 测试景点推荐功能
with app.app_context():
    try:
        print("=== 测试景点推荐功能 ===")
        
        # 加载所有天气数据
        weather_df = load_all_city_data()
        print(f"天气数据加载成功，共 {len(weather_df)} 条记录")
        
        # 初始化推荐服务
        data_dir = os.path.abspath(Config.DATA_DIR)
        recommendation_service = RecommendationService(data_dir)
        
        # 选择一个测试城市
        test_city = "沈阳"
        
        # 测试获取所有景点类型
        attraction_types = recommendation_service.get_attraction_types()
        print(f"景点类型: {attraction_types}")
        
        # 测试获取城市的热门景点
        print(f"\n测试获取 {test_city} 的热门景点...")
        hot_attractions = recommendation_service.get_city_attractions(test_city)
        print(f"获取到 {len(hot_attractions)} 个热门景点")
        
        if not hot_attractions.empty:
            hot_attractions_dict = hot_attractions.to_dict('records')
            print(f"{test_city} 热门景点前5名:")
            for i, rec in enumerate(hot_attractions_dict[:5]):
                print(f"{i+1}. {rec['景点名称']} - 类型: {rec['景点类型']} - 评分: {rec['评分']} - 门票: {rec['门票价格']}元")
        
        # 测试基于天气的景点推荐
        print(f"\n测试基于天气的 {test_city} 景点推荐...")
        weather_recommendations = recommendation_service.recommend_by_weather(weather_df, test_city, "2023-08-01", top_n=10)
        print(f"获取到 {len(weather_recommendations)} 个基于天气的景点推荐")
        
        if not weather_recommendations.empty:
            weather_recommendations_dict = weather_recommendations.to_dict('records')
            print(f"{test_city} 基于天气推荐景点前5名:")
            for i, rec in enumerate(weather_recommendations_dict[:5]):
                print(f"{i+1}. {rec['景点名称']} - 类型: {rec['景点类型']} - 评分: {rec['评分']} - 推荐分数: {rec['推荐分数']:.2f}")
        
        # 测试基于季节的景点推荐
        print(f"\n测试基于季节的 {test_city} 景点推荐...")
        season_recommendations = recommendation_service.recommend_by_season("夏季", test_city, top_n=10)
        print(f"获取到 {len(season_recommendations)} 个基于季节的景点推荐")
        
        if not season_recommendations.empty:
            season_recommendations_dict = season_recommendations.to_dict('records')
            print(f"{test_city} 夏季推荐景点前5名:")
            for i, rec in enumerate(season_recommendations_dict[:5]):
                print(f"{i+1}. {rec['景点名称']} - 类型: {rec['景点类型']} - 评分: {rec['评分']} - 季节匹配分数: {rec['季节匹配分数']:.2f}")
        
        # 测试基于景点类型的推荐
        print(f"\n测试基于景点类型的 {test_city} 景点推荐...")
        type_recommendations = recommendation_service.recommend_by_attraction_type("风景名胜", test_city, top_n=10)
        print(f"获取到 {len(type_recommendations)} 个基于景点类型的推荐")
        
        if not type_recommendations.empty:
            type_recommendations_dict = type_recommendations.to_dict('records')
            print(f"{test_city} 风景名胜类型推荐景点前5名:")
            for i, rec in enumerate(type_recommendations_dict[:5]):
                print(f"{i+1}. {rec['景点名称']} - 类型: {rec['景点类型']} - 评分: {rec['评分']} - 类型匹配分数: {rec['类型匹配分数']:.2f}")
        
        # 测试景点搜索功能
        print(f"\n测试景点搜索功能...")
        search_results = recommendation_service.search_attractions("博物馆", test_city, top_n=10)
        print(f"搜索到 {len(search_results)} 个博物馆相关景点")
        
        if not search_results.empty:
            search_results_dict = search_results.to_dict('records')
            print(f"{test_city} 博物馆相关景点前5名:")
            for i, rec in enumerate(search_results_dict[:5]):
                print(f"{i+1}. {rec['景点名称']} - 类型: {rec['景点类型']} - 评分: {rec['评分']}")
        
        print("\n=== 景点推荐功能测试通过 ===")
        
    except Exception as e:
        print(f"\n=== 景点推荐功能测试失败: {str(e)} ===")
        import traceback
        traceback.print_exc()
