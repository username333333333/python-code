from app import create_app
from app.models import Attraction, TrafficRecord, RiskAssessment
import pandas as pd
import os

app = create_app()

with app.app_context():
    # 连接到数据库
    from app import db
    
    print("开始导入数据...")
    
    # 1. 导入客流量数据
    print("\n1. 开始导入客流量数据...")
    traffic_dir = "data/traffic"
    traffic_files = [f for f in os.listdir(traffic_dir) if f.endswith('.csv')]
    
    total_traffic_records = 0
    for file in traffic_files:
        file_path = os.path.join(traffic_dir, file)
        print(f"  处理文件: {file}")
        
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 遍历每一行数据
            for index, row in df.iterrows():
                # 查找对应的景点
                attraction_name = row['景点名称']
                attraction = Attraction.query.filter_by(name=attraction_name).first()
                
                if attraction:
                    # 创建客流量记录
                    traffic_record = TrafficRecord(
                        attraction_id=attraction.id,
                        date=row['日期'],
                        traffic=int(row['客流量']),
                        is_holiday=bool(row['是否节假日']),
                        weather=row['天气']
                    )
                    db.session.add(traffic_record)
                    total_traffic_records += 1
                    
                    # 每1000条记录提交一次
                    if total_traffic_records % 1000 == 0:
                        db.session.commit()
                        print(f"  已导入 {total_traffic_records} 条客流量记录")
                
        except Exception as e:
            print(f"  处理文件 {file} 时出错: {str(e)}")
    
    # 提交剩余的客流量记录
    db.session.commit()
    print(f"  客流量数据导入完成，共导入 {total_traffic_records} 条记录")
    
    # 2. 导入风险评估数据
    print("\n2. 开始导入风险评估数据...")
    risk_dir = "data/risk"
    risk_files = [f for f in os.listdir(risk_dir) if f.endswith('.csv') and '风险评估数据' in f]
    
    total_risk_records = 0
    for file in risk_files:
        file_path = os.path.join(risk_dir, file)
        print(f"  处理文件: {file}")
        
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 遍历每一行数据
            for index, row in df.iterrows():
                # 查找对应的景点
                attraction_name = row['景点名称']
                attraction = Attraction.query.filter_by(name=attraction_name).first()
                
                if attraction:
                    # 创建风险评估记录
                    risk_assessment = RiskAssessment(
                        attraction_id=attraction.id,
                        date=row['日期'],
                        risk_level=row['风险等级'],
                        advice=row['建议'],
                        weather_forecast={'weather': row['天气']}
                    )
                    db.session.add(risk_assessment)
                    total_risk_records += 1
                    
                    # 每1000条记录提交一次
                    if total_risk_records % 1000 == 0:
                        db.session.commit()
                        print(f"  已导入 {total_risk_records} 条风险评估记录")
                
        except Exception as e:
            print(f"  处理文件 {file} 时出错: {str(e)}")
    
    # 提交剩余的风险评估记录
    db.session.commit()
    print(f"  风险评估数据导入完成，共导入 {total_risk_records} 条记录")
    
    print("\n所有数据导入完成！")
    print(f"最终数据统计：")
    print(f"- 景点数量: {Attraction.query.count()}")
    print(f"- 客流量记录: {TrafficRecord.query.count()}")
    print(f"- 风险评估记录: {RiskAssessment.query.count()}")
