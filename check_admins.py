from app import create_app, db
from app.models import Admin

app = create_app()
with app.app_context():
    print('现有管理员数量:', Admin.query.count())
    print('现有管理员列表:', [(admin.username, admin.email) for admin in Admin.query.all()])
