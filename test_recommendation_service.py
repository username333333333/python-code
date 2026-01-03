#!/usr/bin/env python3
"""
测试RecommendationService是否能正确加载数据
"""

from app.services.recommendation_service import RecommendationService
import os
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).parent
data_dir = BASE_DIR / "data"

print(f"测试数据目录: {data_dir}")

try:
    recommendation_service = RecommendationService(data_dir)
    print("✓ 成功加载景点数据")
    print(f"  数据总行数: {len(recommendation_service.attractions_df)}")
    print(f"  包含城市: {len(recommendation_service.get_all_cities())}")
    print(f"  包含景点类型: {len(recommendation_service.get_attraction_types())}")
    print(f"  城市列表: {recommendation_service.get_all_cities()}")
except Exception as e:
    print(f"✗ 加载景点数据失败: {e}")
    import traceback
    traceback.print_exc()
