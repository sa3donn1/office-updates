import os
import sys
import logging
logging.basicConfig(level=logging.DEBUG)

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, redirect, url_for
from flask_cors import CORS
from src.models.user import db
from src.models.admin import Admin
from src.models.employee import Employee
from src.models.client import Client, Document
from src.models.client_email import ClientEmail
from src.models.power_of_attorney import PowerOfAttorney
from src.models.task import Task
from src.models.attendance import Attendance
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.dashboard import dashboard_bp
from src.routes.clients import clients_bp
from src.routes.employees import employees_bp
from src.routes.tasks import tasks_bp
from src.routes.power_of_attorney import power_of_attorney_bp
from src.routes.reports import reports_bp
from src.routes.ChatBot import chatbot_bp
from src.routes.attendance import attendance_bp 

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(clients_bp, url_prefix='/clients')
app.register_blueprint(employees_bp, url_prefix='/employees')
app.register_blueprint(tasks_bp, url_prefix='/tasks')
app.register_blueprint(power_of_attorney_bp, url_prefix='/power_of_attorney')
app.register_blueprint(reports_bp, url_prefix='/reports')
app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
app.register_blueprint(attendance_bp, url_prefix='/attendance')
# Database configuration
def get_database_path():
    if getattr(sys, 'frozen', False):
        # إذا كان البرنامج .exe
        base_path = os.path.dirname(sys.executable)
        print(f"Running as EXE, base path: {base_path}")
    else:
        # إذا كان البرنامج Python عادي
        base_path = os.path.dirname(__file__)
        print(f"Running as Python, base path: {base_path}")
    
    db_path = os.path.join(base_path, 'database', 'app.db')
    print(f"Database path: {db_path}")
    
    # إنشاء مجلد database إذا لم يكن موجود
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    return f'sqlite:///{db_path}'

app.config['SQLALCHEMY_DATABASE_URI'] = get_database_path()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def create_admin_user():
    """Create default admin user if it doesn't exist"""
    admin = Admin.query.filter_by(username='admin').first()
    if not admin:
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created: admin/admin123")

def create_employee_users():
    """Create default employee users if they don't exist"""
    employees_data = [
        {'employee_id': 'EMP001', 'name': 'مصطفى', 'username': 'mostafa', 'password': 'password123'},
        {'employee_id': 'EMP002', 'name': 'مروة', 'username': 'marwa', 'password': 'password123'},
        {'employee_id': 'EMP003', 'name': 'حفناوي', 'username': 'hefnawy', 'password': 'password123'}
    ]
    for emp_data in employees_data:
        employee = Employee.query.filter_by(username=emp_data['username']).first()
        if not employee:
            employee = Employee(employee_id=emp_data['employee_id'], name=emp_data['name'], username=emp_data['username'])
            employee.set_password(emp_data['password'])
            db.session.add(employee)
            db.session.commit()
            print(f"Default employee user created: {emp_data['username']}/{emp_data['password']}")

with app.app_context():
    db.create_all()
    create_admin_user()
    create_employee_users()

@app.route("/")
def index():
    return redirect(url_for('auth.login'))

@app.route('/<path:path>')
def serve_static(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        return "File not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
