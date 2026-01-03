#!/usr/bin/env python3
"""
初始化脚本：创建第一个管理员用户
"""
import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User

def create_admin():
    """创建管理员用户"""
    app = create_app()
    
    with app.app_context():
        # 检查是否已有管理员用户
        admin = User.query.filter_by(role=User.ROLE_ADMIN).first()
        
        if admin:
            print(f"管理员用户已存在: {admin.username} ({admin.email})")
            return
        
        # 创建管理员用户
        admin_user = User(
            username='admin',
            email='admin@example.com',
            role=User.ROLE_ADMIN
        )
        admin_user.set_password('admin123')
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("管理员用户创建成功！")
        print(f"用户名: admin")
        print(f"邮箱: admin@example.com")
        print(f"密码: admin123")
        print("请登录后及时修改密码！")

if __name__ == '__main__':
    create_admin()
