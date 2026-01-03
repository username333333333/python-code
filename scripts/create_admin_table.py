#!/usr/bin/env python3
"""
初始化脚本：创建管理员表并添加初始管理员用户
"""
import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Admin

def create_admin_table():
    """创建管理员表并添加初始管理员用户"""
    app = create_app()
    
    with app.app_context():
        # 创建所有表（包括新的admin表）
        print("创建数据库表...")
        db.create_all()
        
        # 检查是否已有管理员用户
        admin = Admin.query.first()
        
        if admin:
            print(f"管理员用户已存在: {admin.username} ({admin.email})")
            return
        
        # 创建初始管理员用户
        admin_user = Admin(
            username='admin',
            email='admin@example.com'
        )
        admin_user.set_password('admin123')
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("管理员表创建成功！")
        print("初始管理员用户创建成功！")
        print(f"用户名: admin")
        print(f"邮箱: admin@example.com")
        print(f"密码: admin123")
        print("请登录后及时修改密码！")

if __name__ == '__main__':
    create_admin_table()
