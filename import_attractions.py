from app import create_app
from app.models import Attraction
import pandas as pd
import os
import glob

app = create_app()

with app.app_context():
    # 连接到数据库
    from app import db
    
    print("开始导入景点数据...")
    
    # 1. 导入景点数据
    print("\n1. 开始导入景点数据...")
    poi_dir = "data/poi"
    poi_files = glob.glob(os.path.join(poi_dir, "*_attractions.csv"))
    
    total_attractions = 0
    for file_path in poi_files:
        file = os.path.basename(file_path)
        print(f"  处理文件: {file}")
        
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines='skip')
            
            # 确保列名正确
            df.columns = df.columns.str.strip()
            
            # 遍历每一行数据
            for index, row in df.iterrows():
                # 处理门票价格，将'免费'转换为0
                price_value = row.get('门票价格', 0)
                if pd.notna(price_value):
                    price_value = str(price_value).strip()
                    if price_value == '免费' or price_value == 'Free' or price_value == 'free':
                        price_value = 0.0
                    else:
                        try:
                            price_value = float(price_value)
                        except (ValueError, TypeError):
                            price_value = 0.0
                else:
                    price_value = 0.0
                
                # 处理评分，确保是浮点数
                rating_value = row.get('评分', 0)
                if pd.notna(rating_value):
                    try:
                        rating_value = float(rating_value)
                    except (ValueError, TypeError):
                        rating_value = 0.0
                else:
                    rating_value = 0.0
                
                # 处理经纬度，确保是浮点数，空值保留为None
                longitude_value = row.get('经度')
                if pd.notna(longitude_value) and longitude_value != '' and longitude_value != '，':
                    try:
                        longitude_value = float(longitude_value)
                    except (ValueError, TypeError):
                        longitude_value = None
                else:
                    longitude_value = None
                
                latitude_value = row.get('纬度')
                if pd.notna(latitude_value) and latitude_value != '' and latitude_value != '，':
                    try:
                        latitude_value = float(latitude_value)
                    except (ValueError, TypeError):
                        latitude_value = None
                else:
                    latitude_value = None
                
                # 创建景点对象
                attraction = Attraction(
                    city=row.get('城市', '').strip() if pd.notna(row.get('城市')) else '',
                    name=row.get('景点名称', '').strip() if pd.notna(row.get('景点名称')) else '',
                    type=row.get('类型', '').strip() if pd.notna(row.get('类型')) else '',
                    best_season=row.get('最佳季节', '').strip() if pd.notna(row.get('最佳季节')) else '',
                    rating=rating_value,
                    price=price_value,
                    duration=row.get('推荐游玩时长', '').strip() if pd.notna(row.get('推荐游玩时长')) else '',
                    description=row.get('简介', '').strip() if pd.notna(row.get('简介')) else '',
                    longitude=longitude_value,
                    latitude=latitude_value,
                    phone=row.get('电话', '').strip() if pd.notna(row.get('电话')) else ''
                )
                db.session.add(attraction)
                total_attractions += 1
                
                # 每100条记录提交一次
                if total_attractions % 100 == 0:
                    db.session.commit()
                    print(f"  已导入 {total_attractions} 个景点")
            
        except Exception as e:
            print(f"  处理文件 {file} 时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 提交剩余的景点记录
    db.session.commit()
    print(f"  景点数据导入完成，共导入 {total_attractions} 个景点")
    
    print("\n所有数据导入完成！")
    print(f"最终数据统计：")
    print(f"- 景点数量: {Attraction.query.count()}")
