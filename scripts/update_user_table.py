#!/usr/bin/env python3
"""
初始化脚本：为user表添加nickname和avatar字段
"""
import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

def update_user_table():
    """为user表添加nickname和avatar字段"""
    app = create_app()
    
    with app.app_context():
        # 执行SQL语句添加字段
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                # 检查nickname字段是否存在
                result = conn.execute(text("SHOW COLUMNS FROM user LIKE 'nickname'"))
                if result.fetchone() is None:
                    conn.execute(text('ALTER TABLE user ADD COLUMN nickname VARCHAR(64) DEFAULT \'\''))
                    print("成功为user表添加nickname字段")
                else:
                    print("nickname字段已存在，无需添加")
                
                # 检查avatar字段是否存在
                result = conn.execute(text("SHOW COLUMNS FROM user LIKE 'avatar'"))
                if result.fetchone() is None:
                    conn.execute(text('ALTER TABLE user ADD COLUMN avatar VARCHAR(255) DEFAULT \'\''))
                    print("成功为user表添加avatar字段")
                else:
                    print("avatar字段已存在，无需添加")
                
                conn.commit()
        except Exception as e:
            print(f"更新user表时出错: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    update_user_table()
