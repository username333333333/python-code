#!/usr/bin/env python3
"""
简单的数据库初始化脚本
适合在Render的Shell中直接运行
"""

from app import create_app, db

# 创建应用实例
app = create_app()

with app.app_context():
    try:
        # 创建所有数据库表
        db.create_all()
        print("✅ 所有数据库表创建成功！")
        
        # 检查表是否真的创建成功
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\n📋 创建的表：")
        for table in tables:
            print(f"  - {table}")
        
        print(f"\n总计创建了 {len(tables)} 个表")
    except Exception as e:
        print(f"❌ 数据库表创建失败：{e}")
        import traceback
        traceback.print_exc()