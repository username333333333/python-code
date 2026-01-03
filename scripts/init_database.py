#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本，用于将CSV文件中的景点数据导入到数据库中
"""

import sys
import os
import pandas as pd
from pathlib import Path

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, Attraction, User, Admin, TrafficRecord, RiskAssessment, Itinerary, ItineraryDay, ItineraryAttraction
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, time
import pandas as pd
import os


def init_attractions_data():
    """初始化景点数据"""
    print("开始初始化景点数据...")
    
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        # 检查景点表是否已经有数据
        existing_count = Attraction.query.count()
        if existing_count > 0:
            print(f"景点表已经有 {existing_count} 条数据，跳过初始化")
            return
        
        # 获取数据目录
        data_dir = Path(app.config['DATA_DIR'])
        
        # 优先检查合并的景点数据文件
        combined_file = data_dir / "liaoning_attractions.csv"
        
        # 如果合并文件不存在，检查根目录下的备份文件
        if not combined_file.exists():
            combined_file = Path("liaoning_attractions_backup.csv")
        
        if combined_file.exists():
            print(f"使用合并的景点数据文件: {combined_file}")
            try:
                df = pd.read_csv(combined_file, encoding="utf-8", on_bad_lines='skip')
                
                # 确保列名正确
                df.columns = df.columns.str.strip()
                
                # 只保留需要的列
                required_columns = ['城市', '景点名称', '景点类型', '最佳季节', '评分', 
                                  '门票价格', '推荐游玩时长', '简介', '经度', '纬度', '电话']
                
                # 确保所有需要的列都存在
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = None
                
                total_processed = 0
                
                # 处理每一行数据
                for _, row in df.iterrows():
                    # 处理空值，将NaN转换为None或空字符串
                    name = row['景点名称'] if pd.notna(row['景点名称']) else None
                    city = row['城市'] if pd.notna(row['城市']) else None
                    type = row['景点类型'] if pd.notna(row['景点类型']) else None
                    best_season = row['最佳季节'] if pd.notna(row['最佳季节']) else None
                    description = row['简介'] if pd.notna(row['简介']) else None
                    duration = row['推荐游玩时长'] if pd.notna(row['推荐游玩时长']) else None
                    phone = row['电话'] if pd.notna(row['电话']) else None
                    
                    # 处理门票价格，将'免费'转换为0.0，其他非数值转换为float类型
                    price = row['门票价格']
                    if pd.isna(price):
                        price = 0.0
                    elif isinstance(price, str):
                        # 转换价格字符串
                        if '免费' in price or price.strip() in ['', '免费']:
                            price = 0.0
                        else:
                            # 尝试转换为float
                            try:
                                # 移除可能的货币符号和空格
                                import re
                                price_str = re.sub(r'[\s¥$]', '', price)
                                price = float(price_str)
                            except (ValueError, TypeError):
                                price = 0.0
                    else:
                        price = float(price)
                    
                    # 处理评分，确保是float类型
                    rating = row['评分']
                    if pd.isna(rating):
                        rating = None
                    else:
                        rating = float(rating)
                    
                    # 处理经度和纬度，确保是float类型
                    longitude = None
                    latitude = None
                    if pd.notna(row['经度']):
                        try:
                            longitude = float(row['经度'])
                        except (ValueError, TypeError):
                            longitude = None
                    if pd.notna(row['纬度']):
                        try:
                            latitude = float(row['纬度'])
                        except (ValueError, TypeError):
                            latitude = None
                    
                    # 创建景点对象
                    attraction = Attraction(
                        name=name,
                        city=city,
                        type=type,
                        best_season=best_season,
                        rating=rating,
                        price=price,
                        duration=duration,
                        description=description,
                        longitude=longitude,
                        latitude=latitude,
                        phone=phone
                    )
                    
                    # 添加到数据库
                    db.session.add(attraction)
                    total_processed += 1
                    
                    # 每100条数据提交一次
                    if total_processed % 100 == 0:
                        db.session.commit()
                        print(f"已处理 {total_processed} 条数据")
                
                # 提交剩余的数据
                db.session.commit()
                print(f"景点数据初始化完成，共处理 {total_processed} 条数据")
                return
            except Exception as e:
                print(f"处理合并文件 {combined_file.name} 时出错: {e}")
        
        # 如果合并文件不存在或处理失败，尝试使用按城市分开的文件
        poi_dir = data_dir / "poi"
        
        if not poi_dir.exists():
            print(f"景点数据目录不存在: {poi_dir}")
            return
        
        # 获取所有城市的景点数据文件
        poi_files = list(poi_dir.glob("*_attractions.csv"))
        
        if not poi_files:
            print(f"没有找到景点数据文件: {poi_dir}")
            return
        
        total_processed = 0
        
        # 加载每个城市的景点数据
        for file_path in poi_files:
            try:
                print(f"处理文件: {file_path.name}")
                df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines='skip')
                
                # 确保列名正确
                df.columns = df.columns.str.strip()
                
                # 只保留需要的列
                required_columns = ['城市', '景点名称', '类型', '最佳季节', '评分', 
                                  '门票价格', '推荐游玩时长', '简介', '经度', '纬度', '电话']
                
                # 确保所有需要的列都存在
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = None
                
                # 处理每一行数据
                for _, row in df.iterrows():
                    # 处理空值，将NaN转换为None或空字符串
                    name = row['景点名称'] if pd.notna(row['景点名称']) else None
                    city = row['城市'] if pd.notna(row['城市']) else None
                    type = row['类型'] if pd.notna(row['类型']) else None
                    best_season = row['最佳季节'] if pd.notna(row['最佳季节']) else None
                    description = row['简介'] if pd.notna(row['简介']) else None
                    duration = row['推荐游玩时长'] if pd.notna(row['推荐游玩时长']) else None
                    phone = row['电话'] if pd.notna(row['电话']) else None
                    
                    # 处理门票价格，将'免费'转换为0.0，其他非数值转换为float类型
                    price = row['门票价格']
                    if pd.isna(price):
                        price = 0.0
                    elif isinstance(price, str):
                        # 转换价格字符串
                        if '免费' in price or price.strip() in ['', '免费']:
                            price = 0.0
                        else:
                            # 尝试转换为float
                            try:
                                # 移除可能的货币符号和空格
                                import re
                                price_str = re.sub(r'[\s¥$]', '', price)
                                price = float(price_str)
                            except (ValueError, TypeError):
                                price = 0.0
                    else:
                        price = float(price)
                    
                    # 处理评分，确保是float类型
                    rating = row['评分']
                    if pd.isna(rating):
                        rating = None
                    else:
                        rating = float(rating)
                    
                    # 处理经度和纬度，确保是float类型
                    longitude = None
                    latitude = None
                    if pd.notna(row['经度']):
                        try:
                            longitude = float(row['经度'])
                        except (ValueError, TypeError):
                            longitude = None
                    if pd.notna(row['纬度']):
                        try:
                            latitude = float(row['纬度'])
                        except (ValueError, TypeError):
                            latitude = None
                    
                    # 创建景点对象
                    attraction = Attraction(
                        name=name,
                        city=city,
                        type=type,
                        best_season=best_season,
                        rating=rating,
                        price=price,
                        duration=duration,
                        description=description,
                        longitude=longitude,
                        latitude=latitude,
                        phone=phone
                    )
                    
                    # 添加到数据库
                    db.session.add(attraction)
                    total_processed += 1
                    
                    # 每100条数据提交一次
                    if total_processed % 100 == 0:
                        db.session.commit()
                        print(f"已处理 {total_processed} 条数据")
            
            except Exception as e:
                print(f"处理文件 {file_path.name} 时出错: {e}")
                continue
        
        # 提交剩余的数据
        db.session.commit()
        print(f"景点数据初始化完成，共处理 {total_processed} 条数据")


def init_traffic_records():
    """初始化客流量记录数据"""
    print("开始初始化客流量记录数据...")
    
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        # 检查客流量记录表是否已经有数据
        existing_count = TrafficRecord.query.count()
        if existing_count > 0:
            print(f"客流量记录表已经有 {existing_count} 条数据，跳过初始化")
            return
        
        # 获取数据目录
        data_dir = Path(app.config['DATA_DIR'])
        traffic_dir = data_dir / "traffic"
        
        if not traffic_dir.exists():
            print(f"客流量数据目录不存在: {traffic_dir}")
            return
        
        # 获取所有城市的客流量数据文件
        traffic_files = list(traffic_dir.glob("*_traffic*.csv"))
        
        if not traffic_files:
            print(f"没有找到客流量数据文件: {traffic_dir}")
            return
        
        # 获取所有景点信息，用于映射景点名称到ID
        attractions = Attraction.query.all()
        attraction_map = {(attr.name, attr.city): attr.id for attr in attractions}
        
        total_processed = 0
        
        # 加载每个城市的客流量数据
        for file_path in traffic_files:
            try:
                print(f"处理文件: {file_path.name}")
                df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines='skip')
                
                # 确保列名正确
                df.columns = df.columns.str.strip()
                
                # 只保留需要的列
                required_columns = ['景点名称', '日期', '客流量', '天气', '气温', '是否节假日']
                
                # 确保所有需要的列都存在
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = None
                
                # 获取城市名称（从文件名中提取）
                city = file_path.name.split('_')[0]
                
                # 处理每一行数据
                for _, row in df.iterrows():
                    attraction_name = row['景点名称'] if pd.notna(row['景点名称']) else None
                    if not attraction_name:
                        continue
                    
                    # 获取景点ID
                    attraction_id = attraction_map.get((attraction_name, city))
                    if not attraction_id:
                        continue  # 跳过未找到的景点
                    
                    # 处理日期
                    date_str = row['日期']
                    if not pd.notna(date_str):
                        continue
                    
                    try:
                        date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        continue  # 跳过格式不正确的日期
                    
                    # 处理客流量
                    traffic = row['客流量']
                    if pd.isna(traffic):
                        continue
                    
                    # 处理天气和气温
                    weather = row['天气'] if pd.notna(row['天气']) else None
                    temperature = row['气温'] if pd.notna(row['气温']) else None
                    
                    # 处理是否节假日
                    is_holiday = row['是否节假日'] if pd.notna(row['是否节假日']) else False
                    if isinstance(is_holiday, str):
                        is_holiday = is_holiday.lower() in ['true', '1', 'yes', '是']
                    
                    # 创建客流量记录对象
                    traffic_record = TrafficRecord(
                        attraction_id=attraction_id,
                        date=date,
                        traffic=int(traffic),
                        weather=weather,
                        temperature=temperature if temperature is None else float(temperature),
                        is_holiday=is_holiday
                    )
                    
                    # 添加到数据库
                    db.session.add(traffic_record)
                    total_processed += 1
                    
                    # 每1000条数据提交一次
                    if total_processed % 1000 == 0:
                        db.session.commit()
                        print(f"已处理 {total_processed} 条客流量记录")
            
            except Exception as e:
                print(f"处理文件 {file_path.name} 时出错: {e}")
                continue
        
        # 提交剩余的数据
        db.session.commit()
        print(f"客流量记录数据初始化完成，共处理 {total_processed} 条数据")


def init_users():
    """初始化用户数据"""
    print("开始初始化用户数据...")
    
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        # 检查用户表是否已经有数据
        existing_count = User.query.count()
        if existing_count > 0:
            print(f"用户表已经有 {existing_count} 条数据，跳过初始化")
            return
        
        # 创建默认用户
        default_users = [
            {
                'username': 'user1',
                'email': 'user1@example.com',
                'password': '123456',
                'nickname': '普通用户'
            },
            {
                'username': 'user2',
                'email': 'user2@example.com',
                'password': '123456',
                'nickname': '测试用户'
            }
        ]
        
        for user_data in default_users:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                nickname=user_data['nickname'],
                is_active=True
            )
            user.set_password(user_data['password'])
            db.session.add(user)
        
        db.session.commit()
        print(f"用户数据初始化完成，共创建 {len(default_users)} 个用户")


def init_admin():
    """初始化管理员数据"""
    print("开始初始化管理员数据...")
    
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        # 检查管理员表是否已经有数据
        existing_count = Admin.query.count()
        if existing_count > 0:
            print(f"管理员表已经有 {existing_count} 条数据，跳过初始化")
            return
        
        # 创建默认管理员
        admin = Admin(
            username='admin',
            email='admin@example.com',
            nickname='超级管理员',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("管理员数据初始化完成，创建了默认管理员")


def init_risk_assessments():
    """初始化风险评估数据"""
    print("开始初始化风险评估数据...")
    
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        # 检查风险评估表是否已经有数据
        existing_count = RiskAssessment.query.count()
        if existing_count > 0:
            print(f"风险评估表已经有 {existing_count} 条数据，跳过初始化")
            return
        
        # 获取数据目录
        data_dir = Path(app.config['DATA_DIR'])
        risk_dir = data_dir / "risk"
        
        if not risk_dir.exists():
            print(f"风险评估数据目录不存在: {risk_dir}")
            generate_sample_risk_assessments()
            return
        
        # 获取所有城市的风险评估数据文件
        risk_files = list(risk_dir.glob("*_risk*.csv"))
        
        if not risk_files:
            print(f"没有找到风险评估数据文件: {risk_dir}")
            # 如果没有风险数据文件，生成一些示例数据
            generate_sample_risk_assessments()
            return
        
        # 获取所有景点信息，用于映射景点名称到ID
        attractions = Attraction.query.all()
        attraction_map = {(attr.name, attr.city): attr.id for attr in attractions}
        
        total_processed = 0
        
        # 加载每个城市的风险评估数据
        for file_path in risk_files:
            try:
                print(f"处理文件: {file_path.name}")
                df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines='skip')
                
                # 确保列名正确
                df.columns = df.columns.str.strip()
                
                # 只保留需要的列
                required_columns = ['日期', '景点名称', '风险等级', '天气', '建议']
                
                # 确保所有需要的列都存在
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = None
                
                # 处理每一行数据
                for _, row in df.iterrows():
                    attraction_name = row['景点名称'] if pd.notna(row['景点名称']) else None
                    if not attraction_name:
                        continue
                    
                    # 从文件名获取城市（只适用于沈阳_risk_assessment.csv）
                    if '沈阳' in file_path.name:
                        city = '沈阳'
                    else:
                        # 尝试从景点名称推断城市，或者使用默认值
                        city = None
                        # 遍历所有景点，查找匹配的景点名称和城市
                        for attr_name, attr_city in attraction_map.keys():
                            if attr_name == attraction_name:
                                city = attr_city
                                break
                    
                    if not city:
                        continue  # 跳过无法确定城市的记录
                    
                    # 获取景点ID
                    attraction_id = attraction_map.get((attraction_name, city))
                    if not attraction_id:
                        continue  # 跳过未找到的景点
                    
                    # 处理日期
                    date_str = row['日期']
                    if not pd.notna(date_str):
                        continue
                    
                    try:
                        date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        continue  # 跳过格式不正确的日期
                    
                    # 处理风险等级
                    risk_level = row['风险等级'] if pd.notna(row['风险等级']) else '低'
                    
                    # 处理天气和建议
                    weather = row['天气'] if pd.notna(row['天气']) else None
                    advice = row['建议'] if pd.notna(row['建议']) else None
                    
                    # 构建简单的天气预报
                    weather_forecast = {
                        '天气': weather,
                        '气温': 10 + (date.month % 12) * 2,  # 简单的温度计算
                        '风力': '2级'
                    } if weather else None
                    
                    # 创建风险评估记录对象
                    risk_assessment = RiskAssessment(
                        attraction_id=attraction_id,
                        date=date,
                        risk_level=risk_level,
                        advice=advice,
                        weather_forecast=weather_forecast
                    )
                    
                    # 添加到数据库
                    db.session.add(risk_assessment)
                    total_processed += 1
                    
                    # 每1000条数据提交一次
                    if total_processed % 1000 == 0:
                        db.session.commit()
                        print(f"已处理 {total_processed} 条风险评估记录")
            
            except Exception as e:
                print(f"处理文件 {file_path.name} 时出错: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 如果没有处理任何数据，生成示例数据
        if total_processed == 0:
            print("没有处理任何风险评估数据，生成示例数据...")
            generate_sample_risk_assessments()
            return
        
        # 提交剩余的数据
        db.session.commit()
        print(f"风险评估数据初始化完成，共处理 {total_processed} 条数据")


def generate_sample_risk_assessments():
    """生成示例风险评估数据"""
    print("生成示例风险评估数据...")
    
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        # 获取所有景点
        attractions = Attraction.query.all()
        if not attractions:
            print("没有景点数据，无法生成风险评估数据")
            return
        
        # 生成最近30天的风险评估数据
        today = datetime.now().date()
        risk_levels = ['低', '中', '高']
        weather_conditions = ['晴', '多云', '阴', '小雨', '中雨', '雷阵雨']
        
        total_processed = 0
        
        for attraction in attractions:
            # 为每个景点生成最近30天的风险评估
            for i in range(30):
                date = today - timedelta(days=i)
                
                # 随机选择风险等级
                risk_level = risk_levels[i % 3]
                
                # 生成建议
                advice = f"今日{attraction.name}的风险等级为{risk_level}，建议游客{['正常游玩', '注意安全', '尽量避免前往'][i % 3]}"
                
                # 生成简单的天气预报
                weather_forecast = {
                    '天气': weather_conditions[i % 6],
                    '气温': 15 + i % 10,
                    '风力': f'{i % 5}级'
                }
                
                # 创建风险评估记录
                risk_assessment = RiskAssessment(
                    attraction_id=attraction.id,
                    date=date,
                    risk_level=risk_level,
                    advice=advice,
                    weather_forecast=weather_forecast
                )
                
                db.session.add(risk_assessment)
                total_processed += 1
                
                # 每1000条数据提交一次
                if total_processed % 1000 == 0:
                    db.session.commit()
                    print(f"已生成 {total_processed} 条示例风险评估记录")
        
        # 提交剩余的数据
        db.session.commit()
        print(f"示例风险评估数据生成完成，共生成 {total_processed} 条数据")


def init_sample_itineraries():
    """初始化示例行程数据"""
    print("开始初始化示例行程数据...")
    
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        # 检查行程表是否已经有数据
        existing_count = Itinerary.query.count()
        if existing_count > 0:
            print(f"行程表已经有 {existing_count} 条数据，跳过初始化")
            return
        
        # 获取所有用户和景点
        users = User.query.all()
        if not users:
            print("没有用户数据，无法生成行程数据")
            return
        
        attractions = Attraction.query.all()
        if not attractions:
            print("没有景点数据，无法生成行程数据")
            return
        
        total_processed = 0
        
        # 为每个用户生成2个示例行程
        for user in users:
            for i in range(2):
                # 创建行程
                start_date = datetime.now().date() + timedelta(days=i*7)
                itinerary = Itinerary(
                    user_id=user.id,
                    days=3,
                    start_date=start_date,
                    preferences={
                        'city': attractions[0].city,
                        'attraction_types': ['自然景观', '人文景观'],
                        'budget': 'medium'
                    },
                    status='active' if i == 0 else 'draft'
                )
                db.session.add(itinerary)
                db.session.flush()  # 获取行程ID
                
                # 为行程创建3天的行程安排
                for day_num in range(3):
                    itinerary_day = ItineraryDay(
                        itinerary_id=itinerary.id,
                        day_number=day_num + 1,
                        date=start_date + timedelta(days=day_num),
                        weather='晴'
                    )
                    db.session.add(itinerary_day)
                    db.session.flush()  # 获取行程天数ID
                    
                    # 每天安排3个景点
                    for order in range(3):
                        attraction_index = (i * 10 + day_num * 3 + order) % len(attractions)
                        itinerary_attraction = ItineraryAttraction(
                            itinerary_day_id=itinerary_day.id,
                            attraction_id=attractions[attraction_index].id,
                            order=order + 1,
                            suggested_time=time(9 + order * 3, 0, 0),
                            transportation='步行'
                        )
                        db.session.add(itinerary_attraction)
                        total_processed += 1
                
                # 每10条数据提交一次
                if total_processed % 10 == 0:
                    db.session.commit()
                    print(f"已生成 {total_processed} 条行程景点记录")
        
        # 提交剩余的数据
        db.session.commit()
        print(f"示例行程数据初始化完成，共生成 {total_processed} 条行程景点记录")


def init_all():
    """初始化所有数据"""
    print("开始初始化所有数据...")
    
    init_users()
    init_admin()
    init_attractions_data()
    init_traffic_records()
    init_risk_assessments()
    init_sample_itineraries()
    
    print("所有数据初始化完成！")


if __name__ == "__main__":
    # 解析命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--users":
            init_users()
        elif sys.argv[1] == "--admin":
            init_admin()
        elif sys.argv[1] == "--attractions":
            init_attractions_data()
        elif sys.argv[1] == "--traffic":
            init_traffic_records()
        elif sys.argv[1] == "--risk":
            init_risk_assessments()
        elif sys.argv[1] == "--itineraries":
            init_sample_itineraries()
        else:
            print("用法: python init_database.py [--users|--admin|--attractions|--traffic|--risk|--itineraries]")
    else:
        # 默认初始化所有数据
        init_all()
