from flask import Blueprint, render_template, session, redirect, url_for, flash
from src.models.client import Client
from src.models.employee import Employee
from src.models.task import Task
from src.routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
@login_required
def index():
    if "admin_id" in session:
        clients = Client.query.all()
        employees = Employee.query.all()
        tasks = Task.query.all()
        
        # For statistics cards
        total_clients = len(clients)
        total_employees = len(employees)
        completed_tasks = len([task for task in tasks if task.is_done])
        pending_tasks = len(tasks) - completed_tasks

        stats = {
            "total_clients": total_clients,
            "total_employees": total_employees,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks
        }

        return render_template("dashboard.html", clients=clients, employees=employees, tasks=tasks, stats=stats)
    elif "employee_id" in session:
        # إذا كان موظف، أعد توجيهه إلى لوحة تحكم الموظف
        return redirect(url_for("dashboard.employee_dashboard"))
    else:
        flash("الرجاء تسجيل الدخول أولاً", "warning")
        return redirect(url_for("auth.login"))

@dashboard_bp.route("/employee_dashboard")
@login_required
def employee_dashboard():
    if "employee_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))
        
    employee_id = session["employee_id"]
    employee = Employee.query.get(employee_id)
    
    if not employee:
        flash("حدث خطأ: بيانات الموظف غير موجودة.", "danger")
        return redirect(url_for("auth.login"))

    # هنا يمكنك جلب البيانات الخاصة بالموظف فقط
    # على سبيل المثال، العملاء المعينين له والمهام الخاصة به
    assigned_clients = Client.query.filter_by(employee_id=employee_id).all()
    assigned_tasks = Task.query.filter_by(employee_id=employee_id).all()

    return render_template("employee_dashboard.html", 
                           employee=employee,
                           assigned_clients=assigned_clients,
                           assigned_tasks=assigned_tasks)