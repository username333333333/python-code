#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大数据旅游出行天气决策系统数据收集器
用于获取各类旅游相关数据并分类保存
"""

import os
import json
import random
import requests
import pandas as pd
from datetime import datetime, timedelta
import configparser
from pathlib import Path

# 配置文件路径
CONFIG_FILE = 'config.ini'

def load_config():
    """加载配置文件"""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE, encoding='utf-8')
    return config

# 加载配置
config = load_config()

# 获取API密钥
AMAP_API_KEY = config.get('API', 'AMAP_KEY', fallback='')
CITY_CODE = config.get('CITY', 'CITY_CODE', fallback='210100')  # 沈阳的城市代码

class DataCollector:
    def __init__(self):
        self.amap_api_key = AMAP_API_KEY
        self.city_code = CITY_CODE
        self.base_dir = 'data'
        
        # 创建所有必要的数据目录
        self.data_dirs = ['poi', 'traffic', 'risk', 'itinerary', 'weather_sensitive', 'operation']
        for subdir in self.data_dirs:
            dir_path = os.path.join(self.base_dir, subdir)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"创建目录: {dir_path}")
    
    def get_amap_poi(self, keywords, types, city, page=1, offset=20):
        """使用高德API获取POI数据"""
        url = "https://restapi.amap.com/v3/place/text"
        params = {
            'key': self.amap_api_key,
            'keywords': keywords,
            'types': types,
            'city': city,
            'page': page,
            'offset': offset,
            'output': 'json'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == '1':
                return data.get('pois', []), int(data.get('count', 0))
            else:
                print(f"高德API错误: {data.get('info')}")
                return [], 0
        except Exception as e:
            print(f"获取POI数据失败: {e}")
            return [], 0
    
    def collect_attractions(self, city, types="110000"):
        """收集景点数据（使用原有liaoning_attractions.csv文件）"""
        print(f"正在收集{city}的景点数据...")
        
        # 使用原有景点数据文件
        attractions_file = Path(__file__).parent / 'app' / 'data' / 'liaoning_attractions.csv'
        if not attractions_file.exists():
            print(f"景点数据文件不存在: {attractions_file}")
            return pd.DataFrame()
        
        try:
            # 读取原有数据
            df = pd.read_csv(attractions_file, encoding='utf-8')
            
            # 按城市筛选（处理城市名称格式差异，如"沈阳市" vs "沈阳"）
            # 先将CSV中的城市名称去掉"市"字，再进行匹配
            df['城市'] = df['城市'].str.replace('市', '')
            city_df = df[df['城市'] == city].copy()
            
            # 数据处理：确保列名一致
            if not city_df.empty:
                # 重命名列，确保与原有代码兼容
                if '景点类型' in city_df.columns:
                    city_df.rename(columns={'景点类型': '类型'}, inplace=True)
                
                # 确保'经度'和'纬度'列存在
                if '经度' not in city_df.columns:
                    city_df['经度'] = ''
                if '纬度' not in city_df.columns:
                    city_df['纬度'] = ''
                if '电话' not in city_df.columns:
                    city_df['电话'] = ''
            
            # 保存到指定目录
            output_path = os.path.join(self.base_dir, 'poi', f'{city}_attractions.csv')
            city_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"景点数据已保存到: {output_path}")
            print(f"共收集到{len(city_df)}条{city}景点数据")
            
            return city_df
        except Exception as e:
            print(f"处理景点数据时出错: {e}")
            return pd.DataFrame()
    
    def collect_weather_forecast(self, city, start_year=2013, end_year=2023):
        """生成2013-2023年历史天气数据"""
        print(f"正在生成{city}的{start_year}-{end_year}年历史天气数据...")
        
        # 生成日期范围
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        
        # 模拟天气数据
        weather_data = []
        for date in dates:
            weather = {
                '日期': date.strftime('%Y-%m-%d'),
                '城市': city,
                '最高气温': random.randint(-10, 35),
                '最低气温': random.randint(-20, 25),
                '天气状况': random.choice(['晴', '多云', '阴', '小雨', '中雨', '大雨', '雪']),
                '风力': f'{random.randint(0, 6)}级',
                '降水量': random.randint(0, 100)
            }
            weather_data.append(weather)
        
        # 保存数据
        df = pd.DataFrame(weather_data)
        output_path = os.path.join(self.base_dir, 'weather_sensitive', f'{city}{start_year}-{end_year}年天气数据.csv')
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"{start_year}-{end_year}年天气数据已保存到: {output_path}")
        return df
    
    def collect_transport_data(self, city):
        """收集交通数据"""
        print(f"正在收集{city}的交通数据...")
        
        # 使用高德API获取交通数据
        all_pois = []
        page = 1
        total = 1  # 初始值，用于进入循环
        
        try:
            while True:
                pois, total = self.get_amap_poi("", "150000", city, page)  # 150000是交通设施的类型编码
                if not pois:
                    break
                
                all_pois.extend(pois)
                page += 1
                print(f"已收集{len(all_pois)}/{total}条交通数据")
                
                # 只获取前3页数据，避免过多请求
                if page > 3:
                    break
        except Exception as e:
            print(f"获取交通数据时出错: {e}")
        
        # 数据处理
        transport_data = []
        if all_pois:
            for poi in all_pois[:100]:  # 只保存前100条
                transport = {
                    '名称': poi.get('name', ''),
                    '地址': poi.get('address', ''),
                    '电话': poi.get('tel', ''),
                    '类型': poi.get('type', ''),
                    '城市': poi.get('cityname', '')
                }
                transport_data.append(transport)
        else:
            # 提供默认交通数据
            print(f"未获取到{city}的交通数据，使用默认数据")
            transport_data = [
                {'名称': f'{city}火车站', '地址': f'{city}市中心', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '火车站', '城市': city},
                {'名称': f'{city}机场', '地址': f'{city}郊区', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '机场', '城市': city},
                {'名称': f'{city}长途汽车站', '地址': f'{city}市中心', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '长途汽车站', '城市': city}
            ]
        
        # 保存数据
        df = pd.DataFrame(transport_data)
        output_path = os.path.join(self.base_dir, 'itinerary', f'{city}_transport.csv')
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"交通数据已保存到: {output_path}")
        return df
    
    def collect_catering_data(self, city):
        """收集餐饮数据（添加默认数据支持）"""
        print(f"正在收集{city}的餐饮数据...")
        
        # 使用高德API获取餐饮数据
        all_pois = []
        page = 1
        total = 1  # 初始值，用于进入循环
        
        try:
            while True:
                pois, total = self.get_amap_poi("", "050000", city, page)  # 050000是餐饮服务的类型编码
                if not pois:
                    break
                
                all_pois.extend(pois)
                page += 1
                print(f"已收集{len(all_pois)}/{total}条餐饮数据")
                
                # 只获取前3页数据，避免过多请求
                if page > 3:
                    break
        except Exception as e:
            print(f"获取餐饮数据时出错: {e}")
        
        # 数据处理
        catering_data = []
        if all_pois:
            for poi in all_pois[:100]:  # 只保存前100条
                catering = {
                    '名称': poi.get('name', ''),
                    '地址': poi.get('address', ''),
                    '电话': poi.get('tel', ''),
                    '类型': poi.get('type', ''),
                    '城市': poi.get('cityname', '')
                }
                catering_data.append(catering)
        else:
            # 提供默认餐饮数据
            print(f"未获取到{city}的餐饮数据，使用默认数据")
            default_catering = [
                {'名称': f'{city}风味餐厅', '地址': f'{city}解放路123号', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '中餐', '城市': city},
                {'名称': f'{city}家常菜馆', '地址': f'{city}黄河路456号', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '中餐', '城市': city},
                {'名称': f'{city}火锅一条街', '地址': f'{city}文化路789号', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '火锅', '城市': city},
                {'名称': f'{city}小吃城', '地址': f'{city}民主路321号', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '快餐', '城市': city},
                {'名称': f'{city}烧烤广场', '地址': f'{city}和平路654号', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '烧烤', '城市': city},
                {'名称': f'{city}西餐厅', '地址': f'{city}中央大街987号', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '西餐', '城市': city},
                {'名称': f'{city}海鲜楼', '地址': f'{city}滨海路147号', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '海鲜', '城市': city}
            ]
            catering_data = default_catering
        
        # 保存数据
        df = pd.DataFrame(catering_data)
        output_path = os.path.join(self.base_dir, 'itinerary', f'{city}_catering.csv')
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"餐饮数据已保存到: {output_path}")
        print(f"共收集到{len(catering_data)}条{city}餐饮数据")
        return df
    
    def collect_hotel_data(self, city):
        """收集住宿数据（添加默认数据支持）"""
        print(f"正在收集{city}的住宿数据...")
        
        # 使用高德API获取住宿数据
        all_pois = []
        page = 1
        total = 1  # 初始值，用于进入循环
        
        try:
            while True:
                pois, total = self.get_amap_poi("", "100000", city, page)  # 100000是住宿服务的类型编码
                if not pois:
                    break
                
                all_pois.extend(pois)
                page += 1
                print(f"已收集{len(all_pois)}/{total}条住宿数据")
                
                # 只获取前3页数据，避免过多请求
                if page > 3:
                    break
        except Exception as e:
            print(f"获取住宿数据时出错: {e}")
        
        # 数据处理
        hotel_data = []
        if all_pois:
            for poi in all_pois[:100]:  # 只保存前100条
                hotel = {
                    '名称': poi.get('name', ''),
                    '地址': poi.get('address', ''),
                    '电话': poi.get('tel', ''),
                    '类型': poi.get('type', ''),
                    '城市': poi.get('cityname', '')
                }
                hotel_data.append(hotel)
        else:
            # 提供默认住宿数据
            print(f"未获取到{city}的住宿数据，使用默认数据")
            default_hotels = [
                {'名称': f'{city}大酒店', '地址': f'{city}中央商务区1号', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '豪华酒店', '城市': city},
                {'名称': f'{city}如家快捷酒店', '地址': f'{city}火车站广场东侧', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '经济型酒店', '城市': city},
                {'名称': f'{city}商务酒店', '地址': f'{city}科技园区88号', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '商务酒店', '城市': city},
                {'名称': f'{city}民宿客栈', '地址': f'{city}老城区古街12号', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '民宿', '城市': city},
                {'名称': f'{city}度假山庄', '地址': f'{city}郊外风景区', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '度假酒店', '城市': city},
                {'名称': f'{city}青年旅舍', '地址': f'{city}大学城西门', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '青年旅舍', '城市': city},
                {'名称': f'{city}温泉度假村', '地址': f'{city}温泉镇', '电话': f'0{random.randint(100, 999)}-{random.randint(1000000, 9999999)}', '类型': '温泉酒店', '城市': city}
            ]
            hotel_data = default_hotels
        
        # 保存数据
        df = pd.DataFrame(hotel_data)
        output_path = os.path.join(self.base_dir, 'itinerary', f'{city}_hotel.csv')
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"住宿数据已保存到: {output_path}")
        print(f"共收集到{len(hotel_data)}条{city}住宿数据")
        return df
    
    def generate_traffic_data(self, city, attractions):
        """生成模拟客流量数据（2013-2023年）"""
        print(f"正在生成{city}的2013-2023年模拟客流量数据...")
        
        # 生成2013-2023年的日期范围
        start_date = datetime(2013, 1, 1)
        end_date = datetime(2023, 12, 31)
        dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        
        traffic_data = []
        for attraction in attractions['景点名称'].unique():  # 使用所有景点生成数据
            for date in dates:
                # 模拟客流量数据
                base_traffic = random.randint(500, 5000)
                # 周末客流量增加
                if date.weekday() in [5, 6]:
                    base_traffic *= 1.5
                # 节假日客流量大幅增加
                if date.month in [1, 2, 5, 10] and date.day in [1, 2, 3, 4, 5, 6, 7]:
                    base_traffic *= 2.0
                
                traffic = {
                    '日期': date.strftime('%Y-%m-%d'),
                    '景点名称': attraction,
                    '客流量': int(base_traffic),
                    '是否节假日': 1 if (date.month in [1, 2, 5, 10] and date.day in [1, 2, 3, 4, 5, 6, 7]) else 0,
                    '天气': random.choice(['晴', '多云', '小雨', '中雨', '阴'])
                }
                traffic_data.append(traffic)
        
        # 保存数据
        df = pd.DataFrame(traffic_data)
        output_path = os.path.join(self.base_dir, 'traffic', f'{city}_2013-2023_traffic_data.csv')
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"2013-2023年客流量数据已保存到: {output_path}")
        return df
    
    def generate_risk_data(self, city, attractions):
        """生成模拟风险评估数据（2013-2023年）"""
        print(f"正在生成{city}的2013-2023年模拟风险评估数据...")
        
        # 生成2013-2023年的日期范围
        start_date = datetime(2013, 1, 1)
        end_date = datetime(2023, 12, 31)
        dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        
        risk_data = []
        for attraction in attractions['景点名称'].unique():
            for date in dates:
                # 模拟风险评估数据
                weather = random.choice(['晴', '多云', '阴', '小雨', '中雨', '大雨', '雪'])
                
                # 根据天气状况和景点类型生成风险等级
                risk_level = '低'
                advice = '天气适宜出行'
                
                if weather in ['大雨', '雪']:
                    risk_level = '高'
                    advice = '天气恶劣，建议取消出行'
                elif weather in ['中雨', '阴']:
                    risk_level = '中'
                    advice = '天气一般，建议携带雨具'
                
                risk = {
                    '日期': date.strftime('%Y-%m-%d'),
                    '景点名称': attraction,
                    '风险等级': risk_level,
                    '天气': weather,
                    '建议': advice
                }
                risk_data.append(risk)
        
        # 保存数据
        df = pd.DataFrame(risk_data)
        output_path = os.path.join(self.base_dir, 'risk', f'{city}2013-2023年风险评估数据.csv')
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"2013-2023年风险评估数据已保存到: {output_path}")
        return df
    
    def generate_operation_data(self, city, attractions):
        """生成景区运营决策相关数据"""
        print(f"正在生成{city}的景区运营决策数据...")
        
        # 生成2013-2023年的日期范围
        start_date = datetime(2013, 1, 1)
        end_date = datetime(2023, 12, 31)
        dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        
        operation_data = []
        for attraction in attractions['景点名称'].unique()[:10]:  # 使用前10个景点生成数据
            for date in dates:
                # 模拟景区运营数据
                weather = random.choice(['晴', '多云', '阴', '小雨', '中雨', '大雨', '雪'])
                temperature = random.randint(-10, 35)
                
                # 基于天气和温度生成运营建议
                suggestions = []
                if weather == '晴' and temperature > 25:
                    suggestions.extend([
                        '增加遮阳设施',
                        '准备充足的饮用水',
                        '调整工作人员排班，增加中午时段的人手'
                    ])
                elif weather in ['中雨', '大雨']:
                    suggestions.extend([
                        '准备雨具租赁服务',
                        '检查排水系统',
                        '安排室内活动作为备选'
                    ])
                elif temperature < 0:
                    suggestions.extend([
                        '提供热饮服务',
                        '提醒游客注意保暖',
                        '增加室内休息区'
                    ])
                
                operation = {
                    '日期': date.strftime('%Y-%m-%d'),
                    '景点名称': attraction,
                    '天气状况': weather,
                    '温度': temperature,
                    '建议': ';'.join(suggestions),
                    '预计客流量': random.randint(500, 10000),
                    '最佳营业时间': '09:00-18:00'
                }
                operation_data.append(operation)
        
        # 保存数据
        df = pd.DataFrame(operation_data)
        output_path = os.path.join(self.base_dir, 'operation', f'{city}_operation_data.csv')
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"景区运营决策数据已保存到: {output_path}")
        return df

def main():
    # 辽宁省14个城市
    cities = [
        '沈阳', '大连', '鞍山', '抚顺', '本溪', '丹东',
        '锦州', '营口', '阜新', '辽阳', '盘锦', '铁岭',
        '朝阳', '葫芦岛'
    ]
    
    collector = DataCollector()
    
    # 为每个城市生成2013-2023年的数据
    for city in cities:
        print(f"\n=== 开始处理{city}的数据 ===")
        
        # 收集景点数据
        attractions = collector.collect_attractions(city)
        
        # 如果没有收集到景点数据，尝试从poi目录读取已有的景点数据
        if attractions.empty:
            print(f"尝试从poi目录读取{city}的景点数据...")
            poi_file = Path(__file__).parent / 'data' / 'poi' / f'{city}_attractions.csv'
            if poi_file.exists():
                attractions = pd.read_csv(poi_file, encoding='utf-8')
                print(f"成功从poi目录读取{len(attractions)}条{city}景点数据")
            else:
                print(f"poi目录下没有{city}的景点数据文件")
        
        # 收集2013-2023年历史天气数据
        collector.collect_weather_forecast(city, start_year=2013, end_year=2023)
        
        # 收集交通数据
        collector.collect_transport_data(city)
        
        # 收集餐饮数据
        collector.collect_catering_data(city)
        
        # 收集住宿数据
        collector.collect_hotel_data(city)
        
        # 生成2013-2023年客流量数据
        if not attractions.empty and '景点名称' in attractions.columns:
            collector.generate_traffic_data(city, attractions)
        else:
            print(f"没有收集到有效的景点数据，跳过{city}的客流量数据生成")
        
        # 生成2013-2023年风险评估数据
        if not attractions.empty and '景点名称' in attractions.columns:
            collector.generate_risk_data(city, attractions)
        else:
            print(f"没有收集到有效的景点数据，跳过{city}的风险评估数据生成")
        
        # 生成景区运营决策数据
        if not attractions.empty and '景点名称' in attractions.columns:
            collector.generate_operation_data(city, attractions)
        else:
            print(f"没有收集到有效的景点数据，跳过{city}的景区运营决策数据生成")
    
    print("\n=== 所有城市数据处理完成！ ===")
    print("数据分类说明：")
    print("- data/poi：景点、餐饮、住宿等POI数据")
    print("- data/traffic：2013-2023年客流量预测相关数据")
    print("- data/risk：2013-2023年出行风险评估相关数据")
    print("- data/itinerary：行程规划相关数据")
    print("- data/weather_sensitive：2013-2023年天气敏感型推荐相关数据")
    print("- data/operation：景区运营决策相关数据")

if __name__ == "__main__":
    main()