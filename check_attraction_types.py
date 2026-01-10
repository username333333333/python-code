#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的景点类型
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath('.'))

from app import create_app, db
from app.models import Attraction

def check_attraction_types():
    """检查数据库中的景点类型"""
    print("开始检查数据库中的景点类型...")
    
    # 创建应用实例
    app = create_app()
    
    # 在应用上下文内运行
    with app.app_context():
        # 查询所有不同的景点类型
        attraction_types = db.session.query(Attraction.type).distinct().all()
        
        # 提取类型名称
        types = [type_[0] for type_ in attraction_types if type_[0]]
        
        print(f"数据库中共有 {len(types)} 种不同的景点类型：")
        for i, type_ in enumerate(sorted(types), 1):
            print(f"{i}. {type_}")
        
        # 统计每种类型的景点数量
        print("\n各类型景点数量统计：")
        for type_ in sorted(types):
            count = db.session.query(Attraction).filter(Attraction.type == type_).count()
            print(f"{type_}: {count} 个景点")

if __name__ == "__main__":
    check_attraction_types()
