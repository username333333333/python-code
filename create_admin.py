from app import create_app
from app.models import Admin, db

# 创建Flask应用上下文
app = create_app()
with app.app_context():
    # 直接创建管理员数据，绕过检查逻辑
    print("开始创建管理员数据...")
    
    # 创建默认管理员
    admin = Admin(
        username='admin',
        email='admin@example.com',
        nickname='超级管理员',
        is_active=True
    )
    admin.set_password('admin123')
    
    # 直接添加到数据库
    db.session.add(admin)
    db.session.commit()
    
    print("管理员数据创建完成！")
    print("用户名: admin")
    print("密码: admin123")
