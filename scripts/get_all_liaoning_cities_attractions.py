#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用高德地图API获取辽宁省所有地级市的旅游景点数据
"""

import requests
import pandas as pd
import time


def get_liaoning_city_adcodes():
    """
    获取辽宁省所有地级市的行政区划代码
    
    Returns:
        dict: 城市名称到行政区划代码的映射
    """
    return {
        "沈阳": "210100",
        "大连": "210200",
        "鞍山": "210300",
        "抚顺": "210400",
        "本溪": "210500",
        "丹东": "210600",
        "锦州": "210700",
        "营口": "210800",
        "阜新": "210900",
        "辽阳": "211000",
        "盘锦": "211100",
        "铁岭": "211200",
        "朝阳": "211300",
        "葫芦岛": "211400"
    }


def get_city_attractions(api_key, city_name, adcode, page_size=20, max_pages=50):
    """
    使用高德地图API获取单个城市的旅游景点数据
    
    Args:
        api_key (str): 高德地图API密钥
        city_name (str): 城市名称
        adcode (str): 城市行政区划代码
        page_size (int): 每页返回的结果数量
        max_pages (int): 最大请求页数
    
    Returns:
        list: 包含城市景点信息的列表
    """
    # 高德地图POI搜索API
    url = "https://restapi.amap.com/v3/place/text"
    
    # POI类型：110000-旅游景点
    types = "110000"
    
    city_attractions = []
    
    print(f"开始获取{city_name}市的旅游景点数据...")
    
    # 分页获取数据
    for page in range(1, max_pages + 1):
        params = {
            "key": api_key,
            "keywords": "旅游景点",
            "city": adcode,
            "types": types,
            "offset": page_size,
            "page": page,
            "extensions": "all"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "1":
                print(f"API请求失败，错误信息: {data.get('info', '未知错误')}")
                break
            
            pois = data.get("pois", [])
            if not pois:
                print(f"{city_name}市没有更多数据了")
                break
            
            print(f"正在处理{city_name}市第{page}页，获取到{len(pois)}个景点")
            
            # 解析每个景点的数据
            for poi in pois:
                # 处理评分字段，可能返回列表
                rating = poi.get("biz_ext", {}).get("rating", 0)
                if isinstance(rating, list):
                    rating = rating[0] if rating else 0
                
                # 处理门票价格字段
                cost = poi.get("biz_ext", {}).get("cost", "免费")
                if isinstance(cost, list):
                    cost = cost[0] if cost else "免费"
                
                # 提取经纬度信息
                location = poi.get("location", "")
                longitude = latitude = ""
                if location:
                    lon_lat = location.split(",")
                    if len(lon_lat) == 2:
                        longitude = lon_lat[0]
                        latitude = lon_lat[1]
                
                attraction = {
                    "城市": poi.get("cityname", city_name + "市"),
                    "景点名称": poi.get("name", ""),
                    "景点类型": poi.get("type", "").split(";"),  # 类型格式：大类;中类;小类
                    "最佳季节": "全年",  # 高德API不直接提供，默认设为全年
                    "评分": float(rating),
                    "门票价格": cost,
                    "推荐游玩时长": "2-3小时",  # 高德API不直接提供，默认设为2-3小时
                    "简介": poi.get("address", ""),  # 使用地址作为简介，实际项目中可补充
                    "经度": longitude,
                    "纬度": latitude
                }
                
                # 处理景点类型，只保留大类
                if isinstance(attraction["景点类型"], list) and len(attraction["景点类型"]) > 0:
                    attraction["景点类型"] = attraction["景点类型"][0]
                else:
                    attraction["景点类型"] = "景点"
                
                city_attractions.append(attraction)
            
            # 避免请求过于频繁，暂停1秒
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            print(f"请求出错: {e}")
            break
    
    print(f"{city_name}市数据获取完成，共获取到{len(city_attractions)}个景点")
    return city_attractions


def save_to_csv(df, file_path):
    """
    将DataFrame保存为CSV文件
    
    Args:
        df (pd.DataFrame): 包含景点信息的DataFrame
        file_path (str): 保存路径
    """
    try:
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        print(f"数据已成功保存到: {file_path}")
    except Exception as e:
        print(f"保存文件失败: {e}")


if __name__ == "__main__":
    # 高德地图API密钥
    API_KEY = "6a978d868f477c8159aa4fc1c6f3b9f6"
    
    # 获取辽宁省所有地级市的行政区划代码
    city_adcodes = get_liaoning_city_adcodes()
    
    all_attractions = []
    
    # 逐个城市获取景点数据
    for city_name, adcode in city_adcodes.items():
        city_attractions = get_city_attractions(API_KEY, city_name, adcode)
        all_attractions.extend(city_attractions)
        # 城市间暂停2秒，避免请求过于频繁
        time.sleep(2)
    
    if all_attractions:
        # 创建DataFrame
        df = pd.DataFrame(all_attractions)
        
        # 数据去重
        df = df.drop_duplicates(subset=['景点名称', '城市'], keep='first')
        
        print(f"\n所有城市数据获取完成，共获取到{len(df)}个景点")
        
        # 显示数据前10行，包含不同城市的数据
        print("\n数据示例:")
        # 随机选择10行，确保包含不同城市
        if len(df) >= 10:
            print(df.sample(10))
        else:
            print(df)
        
        # 显示各城市景点数量
        print("\n各城市景点数量:")
        print(df['城市'].value_counts())
        
        # 保存到app/data目录下
        output_path = "app/data/liaoning_attractions.csv"
        save_to_csv(df, output_path)
        
        # 也保存到根目录作为备份
        save_to_csv(df, "liaoning_attractions_backup.csv")
    else:
        print("未获取到任何数据，请检查API密钥是否正确")
