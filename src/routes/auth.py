from flask import Blueprint, request, session, redirect, url_for, render_template, flash, jsonify
from src.models.admin import Admin
from src.models.employee import Employee
from src.models.user import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # محاولة تسجيل الدخول كآدمين
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session["admin_id"] = admin.id
            session["admin_username"] = admin.username
            flash("تم تسجيل الدخول بنجاح كمسؤول", "success")
            return redirect(url_for("dashboard.index"))
        
        # إذا لم يكن آدمين، حاول تسجيل الدخول كموظف
        employee = Employee.query.filter_by(username=username).first()
        if employee and employee.check_password(password):
            session["employee_id"] = employee.id
            session["employee_username"] = employee.username
            flash("تم تسجيل الدخول بنجاح كموظف", "success")
            return redirect(url_for("dashboard.employee_dashboard"))
        
        # إذا فشل تسجيل الدخول كآدمين أو موظف
        flash("اسم المستخدم أو كلمة المرور غير صحيحة", "error")
    
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.pop("admin_id", None)
    session.pop("admin_username", None)
    session.pop("employee_id", None)
    session.pop("employee_username", None)
    flash("تم تسجيل الخروج بنجاح", "success")
    return redirect(url_for("auth.login"))

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session and "employee_id" not in session:
            flash("الرجاء تسجيل الدخول أولاً", "warning")
            return redirect(url_for("auth.login")) 
        return f(*args, **kwargs)
    return decorated_function

