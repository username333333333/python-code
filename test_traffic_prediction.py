#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试客流量预测服务
"""

import sys
import os
from app.services.traffic_prediction_service import TrafficPredictionServiceFactory

def test_traffic_prediction_service():
    """测试客流量预测服务"""
    print("=== 测试客流量预测服务 ===")
    
    # 创建客流量预测服务实例
    data_dir = os.path.join(os.getcwd(), "data")
    traffic_service = TrafficPredictionServiceFactory.create_service("sklearn", data_dir)
    
    # 测试1：获取景点列表
    print("\n1. 测试获取景点列表...")
    try:
        attractions = traffic_service.get_attraction_list()
        print(f"   成功获取景点列表，共 {len(attractions)} 个景点")
        if attractions:
            print(f"   前5个景点：{attractions[:5]}")
    except Exception as e:
        print(f"   失败：{str(e)}")
    
    # 测试2：获取城市景点
    print("\n2. 测试获取城市景点...")
    try:
        city_attractions = traffic_service.get_city_attractions("大连")
        print(f"   成功获取大连景点，共 {len(city_attractions)} 个景点")
        if city_attractions:
            print(f"   前5个大连景点：{city_attractions[:5]}")
    except Exception as e:
        print(f"   失败：{str(e)}")
    
    # 测试3：训练模型
    print("\n3. 测试训练模型...")
    try:
        training_results = traffic_service.train_all_models()
        success_count = len([r for r in training_results.values() if 'error' not in r])
        fail_count = len([r for r in training_results.values() if 'error' in r])
        print(f"   模型训练完成：成功 {success_count} 个，失败 {fail_count} 个")
        
        # 打印部分训练结果
        print("   部分训练结果：")
        for attraction, result in list(training_results.items())[:3]:
            if 'error' in result:
                print(f"     {attraction}: 失败 - {result['error']}")
            else:
                print(f"     {attraction}: MSE={result['mse']:.2f}, RMSE={result['rmse']:.2f}, 样本数={result['samples']}")
    except Exception as e:
        print(f"   失败：{str(e)}")
    
    # 测试4：预测未来客流量
    print("\n4. 测试预测未来客流量...")
    try:
        # 使用第一个景点作为测试
        attractions = traffic_service.get_attraction_list()
        if attractions:
            test_attraction = attractions[0]
            # 创建模拟天气预报数据
            weather_forecast = [
                {
                    "日期": "2025-12-28",
                    "最高气温": 10,
                    "最低气温": 0,
                    "降水量": 0,
                    "风力": 2,
                    "天气状况": "晴"
                },
                {
                    "日期": "2025-12-29",
                    "最高气温": 8,
                    "最低气温": -2,
                    "降水量": 5,
                    "风力": 3,
                    "天气状况": "小雨"
                },
                {
                    "日期": "2025-12-30",
                    "最高气温": 12,
                    "最低气温": 2,
                    "降水量": 0,
                    "风力": 1,
                    "天气状况": "多云"
                }
            ]
            
            predictions = traffic_service.predict_future_traffic(test_attraction, weather_forecast)
            print(f"   成功预测 {test_attraction} 未来3天客流量")
            for pred in predictions:
                print(f"     {pred['date']}: {pred['traffic']} 人次, 天气: {pred['weather']}")
    except Exception as e:
        print(f"   失败：{str(e)}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_traffic_prediction_service()