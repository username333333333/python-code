from app import create_app
from app.services.risk_assessment_service import RiskAssessmentService
import os
from app.config import Config

app = create_app()

# 测试风险评估服务
with app.app_context():
    try:
        print("=== 测试出行准备功能 - 风险评估服务 ===")
        
        # 初始化风险评估服务
        data_dir = os.path.abspath(Config.DATA_DIR)
        risk_service = RiskAssessmentService(data_dir)
        print("风险评估服务初始化成功")
        
        # 测试景点类型分类
        print("\n测试景点类型分类功能...")
        
        # 测试不同类型的景点分类
        test_cases = [
            ("沈阳故宫", "沈阳故宫是中国现存的两座古代宫殿建筑群之一，是清朝初期的皇宫"),
            ("沈阳植物园", "沈阳植物园是一座大型综合性植物园，展示了大量的植物品种"),
            ("棋盘山", "棋盘山是沈阳著名的山地景区，适合登山和户外活动"),
            ("沈阳海洋馆", "沈阳海洋馆是一座室内海洋主题乐园，展示了各种海洋生物"),
            ("东北亚滑雪场", "东北亚滑雪场是沈阳著名的滑雪胜地，冬季开放")
        ]
        
        for attraction_name, attraction_desc in test_cases:
            attraction_type = risk_service.classify_attraction_type(attraction_name, attraction_desc)
            print(f"{attraction_name} -> 类型: {attraction_type}")
        
        # 测试风险评估功能
        print("\n测试风险评估功能...")
        
        # 准备测试数据
        test_weather_forecast = {
            'weather': '晴',
            'temperature': '25℃',  # 字符串类型的温度，测试修复后的功能
            'wind': '5级',  # 字符串类型的风速，测试修复后的功能
            'precipitation': '0mm'  # 字符串类型的降水量，测试修复后的功能
        }
        
        # 测试不同类型景点的风险评估
        attraction_types = ['山地', '海滨', '户外', '室内', '主题乐园', '博物馆', '温泉', '滑雪']
        
        for attr_type in attraction_types:
            risk_result = risk_service.assess_risk(attr_type, test_weather_forecast)
            print(f"{attr_type} -> 风险等级: {risk_result['risk_level']} - 建议: {risk_result['advice'][0]}")
        
        # 测试生成风险报告
        print("\n测试生成风险报告功能...")
        
        # 准备天气预报数据
        weather_forecasts = [
            {
                'date': '2023-08-01',
                'weather': '晴',
                'temperature': '30℃',
                'wind': '3级',
                'precipitation': '0mm'
            },
            {
                'date': '2023-08-02',
                'weather': '多云',
                'temperature': '28℃',
                'wind': '4级',
                'precipitation': '0mm'
            },
            {
                'date': '2023-08-03',
                'weather': '雷阵雨',
                'temperature': '25℃',
                'wind': '6级',
                'precipitation': '30mm'
            }
        ]
        
        # 生成风险评估报告
        risk_report = risk_service.generate_risk_report(
            attraction_name="棋盘山",
            attraction_desc="棋盘山是沈阳著名的山地景区，适合登山和户外活动",
            weather_forecasts=weather_forecasts
        )
        
        print(f"风险报告生成成功")
        print(f"景点名称: {risk_report['attraction_name']}")
        print(f"景点类型: {risk_report['attraction_type']}")
        print(f"总天数: {risk_report['summary']['total_days']}")
        print(f"安全天数: {risk_report['summary']['safe_days']}")
        print(f"风险分布: 低风险 {risk_report['summary']['risk_distribution']['低']}天, 中风险 {risk_report['summary']['risk_distribution']['中']}天, 高风险 {risk_report['summary']['risk_distribution']['高']}天")
        
        print("\n=== 出行准备功能测试通过 ===")
        
    except Exception as e:
        print(f"\n=== 出行准备功能测试失败: {str(e)} ===")
        import traceback
        traceback.print_exc()
