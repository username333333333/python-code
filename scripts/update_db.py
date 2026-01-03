#!/usr/bin/env python3
"""
数据库更新脚本：为user表添加role字段
"""
import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db


def update_database():
    """更新数据库，为user表添加role字段"""
    app = create_app()
    
    with app.app_context():
        # 执行SQL语句添加role字段
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                # 首先检查字段是否存在
                result = conn.execute(text("SHOW COLUMNS FROM user LIKE 'role'"))
                if result.fetchone() is None:
                    conn.execute(text('ALTER TABLE user ADD COLUMN role INT DEFAULT 0'))
                    conn.commit()
                    print("成功为user表添加role字段")
                else:
                    print("role字段已存在，无需添加")
        except Exception as e:
            print(f"添加role字段时出错: {e}")
            print("可能字段已存在，继续执行")


if __name__ == '__main__':
    update_database()
