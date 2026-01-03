from app import create_app
from app.models import Admin, db

# 创建Flask应用上下文
app = create_app()
with app.app_context():
    # 测试管理员数据是否存在
    print("开始测试管理员数据...")
    
    # 检查管理员表中是否有数据
    admin_count = Admin.query.count()
    print(f"管理员表中的数据数量: {admin_count}")
    
    # 获取管理员数据
    admin = Admin.query.filter_by(username='admin').first()
    if admin:
        print("管理员数据存在！")
        print(f"用户名: {admin.username}")
        print(f"邮箱: {admin.email}")
        print(f"昵称: {admin.nickname}")
        print(f"是否活跃: {admin.is_active}")
        
        # 测试密码是否正确
        if admin.check_password('admin123'):
            print("密码验证通过！")
        else:
            print("密码验证失败！")
    else:
        print("管理员数据不存在！")
