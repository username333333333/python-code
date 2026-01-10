#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试旅游决策中心的行程管理功能
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 配置WebDriver（需要安装ChromeDriver并添加到PATH）
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 无头模式，不显示浏览器窗口
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

def test_tourism_itinerary():
    """测试旅游决策中心的行程管理功能"""
    print("=" * 60)
    print("开始测试旅游决策中心的行程管理功能...")
    print("=" * 60)
    
    try:
        # 初始化WebDriver
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1920, 1080)  # 设置窗口大小，确保元素可见
        
        # 访问旅游决策中心页面
        driver.get("http://127.0.0.1:5000/tourism_decision_center/")
        time.sleep(2)  # 等待页面加载
        
        # 选择目的地
        print("步骤1: 选择目的地")
        # 找到第一个城市的"选择"按钮并点击
        select_button = driver.find_element(By.XPATH, "//a[contains(@class, 'btn-primary') and text()='选择']")
        select_button.click()
        time.sleep(2)
        
        # 获取景点推荐
        print("步骤2: 获取景点推荐")
        # 找到"获取景点推荐"按钮并点击
        recommend_button = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-success') and text()='获取景点推荐']")
        recommend_button.click()
        time.sleep(3)  # 等待推荐结果加载
        
        # 添加多个景点到行程
        print("步骤3: 添加多个景点到行程")
        # 找到所有"添加到行程"按钮
        add_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'add-to-itinerary')]")
        
        if len(add_buttons) < 3:
            print(f"❌ 只找到 {len(add_buttons)} 个'添加到行程'按钮，不足以进行测试")
            return False
        
        # 添加前3个景点到行程
        added_count = 0
        for i in range(3):
            try:
                # 点击"添加到行程"按钮
                add_buttons[i].click()
                time.sleep(1)
                
                # 处理确认对话框
                alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
                alert.accept()
                time.sleep(1)
                
                # 处理成功提示对话框
                success_alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
                success_alert.accept()
                time.sleep(1)
                
                added_count += 1
                print(f"✅ 成功添加第 {i+1} 个景点到行程")
            except Exception as e:
                print(f"❌ 添加第 {i+1} 个景点失败: {str(e)}")
                continue
        
        if added_count < 2:
            print(f"❌ 只成功添加了 {added_count} 个景点，不足以进行测试")
            return False
        
        # 进入行程规划步骤
        print("步骤4: 进入行程规划步骤")
        # 找到"下一步"按钮并点击，进入步骤2
        next_button = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-primary') and text()='下一步']")
        next_button.click()
        time.sleep(2)
        
        # 再次点击"下一步"按钮，进入步骤3（行程规划）
        next_button.click()
        time.sleep(2)
        
        # 检查行程中的景点数量
        print("步骤5: 检查行程中的景点数量")
        # 等待行程列表加载
        itinerary_list = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "itinerary-items-list")))
        time.sleep(1)
        
        # 统计行程中的景点数量
        itinerary_items = driver.find_elements(By.XPATH, "//ul[@class='list-group']/li")
        print(f"✅ 行程中共有 {len(itinerary_items)} 个景点")
        
        # 验证行程中的景点数量是否与添加的数量一致
        if len(itinerary_items) == added_count:
            print(f"✅ 测试成功！行程中显示的景点数量与添加的数量一致")
            return True
        else:
            print(f"❌ 测试失败！添加了 {added_count} 个景点，但行程中只显示了 {len(itinerary_items)} 个")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 关闭浏览器
        driver.quit()

if __name__ == "__main__":
    test_tourism_itinerary()