#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置景点数据脚本
删除所有景点数据，然后重新导入
"""

from app import create_app
from app.models import Attraction
import os

app = create_app()

with app.app_context():
    # 连接到数据库
    from app import db
    
    print("开始重置景点数据...")
    
    # 1. 删除所有景点数据
    print("\n1. 删除所有景点数据...")
    try:
        # 删除所有景点
        Attraction.query.delete()
        db.session.commit()
        print(f"  成功删除所有景点数据")
        print(f"  当前景点数量: {Attraction.query.count()}")
    except Exception as e:
        print(f"  删除景点数据失败: {str(e)}")
        db.session.rollback()
    
    print("\n2. 重新导入景点数据...")
    # 调用import_attractions.py脚本
    os.system("python import_attractions.py")
    
    print("\n3. 验证导入结果...")
    print(f"  最终景点数量: {Attraction.query.count()}")
    print("\n景点数据重置完成！")
