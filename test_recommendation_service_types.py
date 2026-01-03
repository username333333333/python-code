from app.services.recommendation_service import RecommendationService
import pandas as pd
import os

# 获取当前项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))

def test_attraction_types():
    """测试推荐服务的景点类型筛选功能"""
    try:
        # 创建推荐服务实例，传入正确的数据目录
        data_dir = os.path.join(project_root, 'data')
        recommendation_service = RecommendationService(data_dir)
        
        # 打印所有景点数据的前10行，检查数据加载情况
        print("所有景点数据前10行:")
        print(recommendation_service.attractions_df.head(10))
        print(f"\n总景点数量: {len(recommendation_service.attractions_df)}")
        
        # 检查沈阳的景点数据
        shenyang_attractions = recommendation_service.attractions_df[recommendation_service.attractions_df['城市'] == '沈阳']
        print(f"\n沈阳景点数量: {len(shenyang_attractions)}")
        print("沈阳景点前10行:")
        print(shenyang_attractions.head(10))
        
        # 测试景点类型筛选
        print("\n=== 测试景点类型筛选 ===")
        
        # 空的天气数据
        weather_df = pd.DataFrame()
        
        # 测试各种景点类型
        test_types = ['博物馆', '公园', '风景区', '历史古迹', '温泉', '冰雪']
        
        for attraction_type in test_types:
            print(f"\n--- 测试类型: {attraction_type} ---")
            recommendations = recommendation_service.recommend_by_weather(
                weather_df=weather_df,
                city='沈阳',
                top_n=5,
                attraction_types=[attraction_type]
            )
            
            print(f"推荐数量: {len(recommendations)}")
            if not recommendations.empty:
                print("推荐景点:")
                for idx, row in recommendations.iterrows():
                    print(f"  {row['景点名称']} - 类型: {row['景点类型']}")
            else:
                print("没有找到匹配的景点")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_attraction_types()
