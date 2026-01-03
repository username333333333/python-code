#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新登录历史表结构，添加fail_reason字段支持登录失败原因记录
"""

import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app import db
from app.models import LoginHistory


def update_login_history_table():
    """更新登录历史表结构"""
    print("开始更新登录历史表结构...")
    
    # 创建应用实例和上下文
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # 开始事务
                with conn.begin():
                    # 添加fail_reason字段
                    print("添加fail_reason字段...")
                    conn.execute(db.text('ALTER TABLE login_history ADD COLUMN fail_reason VARCHAR(100) NULL;'))
            
            print("登录历史表结构更新成功！")
            return True
        except Exception as e:
            print(f"更新失败: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    update_login_history_table()
