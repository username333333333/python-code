from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    print('现有用户数量:', User.query.count())
    print('现有用户列表:', [user.username for user in User.query.all()])
