from flask import Flask
from .models.user import db
from .models.admin import Admin
from .models.client import Client
from .models.task import Task
from .models.task_attachment import TaskAttachment
from .models.employee import Employee

def init_db():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    db.init_app(app)
    
    with app.app_context():
        # حذف كل الجداول وإعادة إنشائها
        db.drop_all()
        db.create_all()
        
        # إضافة admin أولي
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    init_db()
    print("تم تهيئة قاعدة البيانات بنجاح!")