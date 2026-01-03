#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新收藏表结构，添加admin_id字段支持管理员收藏
"""

import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app import db
from app.models import Favorite


def update_favorite_table():
    """更新收藏表结构"""
    print("开始更新收藏表结构...")
    
    # 创建应用实例和上下文
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # 开始事务
                with conn.begin():
                    # 1. 修改user_id字段为可为空
                    print("修改user_id字段为可为空...")
                    conn.execute(db.text('ALTER TABLE favorite MODIFY COLUMN user_id INT NULL;'))
                    
                    # 2. 添加admin_id字段
                    print("添加admin_id字段...")
                    conn.execute(db.text('ALTER TABLE favorite ADD COLUMN admin_id INT NULL;'))
                    
                    # 3. 添加外键约束
                    print("添加外键约束...")
                    conn.execute(db.text('ALTER TABLE favorite ADD CONSTRAINT fk_favorite_admin FOREIGN KEY (admin_id) REFERENCES admin(id);'))
            
            print("收藏表结构更新成功！")
            return True
        except Exception as e:
            print(f"更新失败: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    update_favorite_table()
