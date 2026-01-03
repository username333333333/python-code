from app import create_app, db
from app.models import *

app = create_app()

with app.app_context():
    print('Tables in database:', db.metadata.tables.keys())
    print('\nChecking data counts:')
    for table in db.metadata.tables.keys():
        count = db.session.query(db.metadata.tables[table]).count()
        print(f'{table}: {count}')
