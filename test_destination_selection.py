from app import create_app
from app.services.recommendation_service import RecommendationService
from app.utils.data_loader import load_all_city_data
import os
from app.config import Config

app = create_app()

# 测试城市推荐指数计算功能
with app.app_context():
    try:
        print("=== 测试目的地选择功能 ===")
        
        # 加载所有天气数据
        weather_df = load_all_city_data()
        print(f"天气数据加载成功，共 {len(weather_df)} 条记录")
        
        # 初始化推荐服务
        data_dir = os.path.abspath(Config.DATA_DIR)
        recommendation_service = RecommendationService(data_dir)
        
        # 测试获取所有城市
        cities = recommendation_service.get_all_cities()
        print(f"获取城市列表成功，共 {len(cities)} 个城市")
        print(f"城市列表: {cities}")
        
        # 测试获取景点类型
        attraction_types = recommendation_service.get_attraction_types()
        print(f"获取景点类型成功，共 {len(attraction_types)} 种类型")
        print(f"景点类型: {attraction_types}")
        
        # 测试计算城市推荐指数（无出行日期）
        print("\n测试计算城市推荐指数（无出行日期）...")
        city_scores = recommendation_service.calculate_city_travel_score(weather_df, "")
        print(f"城市推荐指数计算成功，共 {len(city_scores)} 个城市")
        
        if not city_scores.empty:
            city_scores_dict = city_scores.to_dict('records')
            print("城市推荐指数列表:")
            for i, city in enumerate(city_scores_dict[:5]):  # 只显示前5个城市
                print(f"{i+1}. {city['城市']} - 推荐指数: {city['平均旅游评分']} - {city.get('推荐指数', '未知')}")
        
        # 测试计算城市推荐指数（有出行日期）
        print("\n测试计算城市推荐指数（有出行日期）...")
        city_scores_with_date = recommendation_service.calculate_city_travel_score(weather_df, "2023-08-01")
        print(f"城市推荐指数计算成功，共 {len(city_scores_with_date)} 个城市")
        
        if not city_scores_with_date.empty:
            city_scores_with_date_dict = city_scores_with_date.to_dict('records')
            print("带日期的城市推荐指数列表:")
            for i, city in enumerate(city_scores_with_date_dict[:5]):  # 只显示前5个城市
                print(f"{i+1}. {city['城市']} - 推荐指数: {city['平均旅游评分']} - {city.get('推荐指数', '未知')}")
        
        print("\n=== 目的地选择功能测试通过 ===")
        
    except Exception as e:
        print(f"\n=== 目的地选择功能测试失败: {str(e)} ===")
        import traceback
        traceback.print_exc()
