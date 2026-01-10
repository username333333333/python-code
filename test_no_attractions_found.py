#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试当未找到符合条件的景点时的系统行为
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath('.'))

from app import create_app

def test_no_attractions_found():
    """测试当未找到符合条件的景点时，系统是否能正确返回提示信息"""
    print("开始测试当未找到符合条件的景点时的系统行为...")
    
    # 创建应用实例
    app = create_app()
    
    # 创建测试客户端
    client = app.test_client()
    
    # 测试用例：选择一个不存在的景点类型
    test_cases = [
        {
            "name": "不存在的景点类型",
            "start_city": "沈阳",
            "target_city": "沈阳",
            "days": 3,
            "preferences": {
                "attraction_types": ["不存在的类型"]
            },
            "expected_success": False,
            "expected_message": "未找到符合您偏好的景点"
        },
        {
            "name": "多个不存在的景点类型",
            "start_city": "沈阳",
            "target_city": "沈阳",
            "days": 3,
            "preferences": {
                "attraction_types": ["不存在的类型1", "不存在的类型2"]
            },
            "expected_success": False,
            "expected_message": "未找到符合您偏好的景点"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- 测试 {test_case['name']} ---")
        
        # 发送请求
        response = client.post(
            '/path/optimize',
            json={
                "start_city": test_case["start_city"],
                "target_city": test_case["target_city"],
                "days": test_case["days"],
                "preferences": test_case["preferences"]
            }
        )
        
        # 解析响应
        result = response.get_json()
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应结果: {result}")
        
        # 验证结果
        if result["success"] == test_case["expected_success"]:
            print(f"✓ 成功状态验证通过")
        else:
            print(f"✗ 成功状态验证失败，期望: {test_case['expected_success']}, 实际: {result['success']}")
        
        if test_case["expected_message"] in result.get("message", ""):
            print(f"✓ 错误信息验证通过")
        else:
            print(f"✗ 错误信息验证失败，期望包含: {test_case['expected_message']}, 实际: {result.get('message')}")
        
        if not result["itinerary"]:
            print(f"✓ 行程列表为空验证通过")
        else:
            print(f"✗ 行程列表应为空，实际: {len(result['itinerary'])} 天")
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_no_attractions_found()
