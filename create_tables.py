from app import create_app, db

# 创建Flask应用上下文
app = create_app()
with app.app_context():
    # 创建所有数据库表
    db.create_all()
    print("数据库表创建完成！")
