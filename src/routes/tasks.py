from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta, date
from src.routes.auth import login_required
from src.models.task import Task
from src.models.employee import Employee
from src.models.user import db

tasks_bp = Blueprint("tasks", __name__)

@tasks_bp.route("/")
@login_required
def index():
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))
    
    # الحصول على معاملات الفلترة
    time_filter = request.args.get("time_filter", "all", type=str)
    custom_date = request.args.get("custom_date", "", type=str)
    
    # بناء الاستعلام مع الترتيب من الجديد للقديم
    query = Task.query.order_by(Task.created_at.desc())
    
    # تطبيق الفلاتر الزمنية
    now = datetime.utcnow()
    today = date.today()
    
    if time_filter == "today":
        # اليوم
        start_of_day = datetime.combine(today, datetime.min.time())
        query = query.filter(Task.created_at >= start_of_day)
    
    elif time_filter == "this_week":
        # هذا الأسبوع (آخر 7 أيام)
        one_week_ago = now - timedelta(days=7)
        query = query.filter(Task.created_at >= one_week_ago)
    
    elif time_filter == "this_month":
        # هذا الشهر (آخر 30 يوم)
        one_month_ago = now - timedelta(days=30)
        query = query.filter(Task.created_at >= one_month_ago)
    
    elif custom_date:
        # تاريخ مخصص
        try:
            custom_date_obj = datetime.strptime(custom_date, "%Y-%m-%d").date()
            start_of_day = datetime.combine(custom_date_obj, datetime.min.time())
            end_of_day = datetime.combine(custom_date_obj, datetime.max.time())
            query = query.filter(Task.created_at.between(start_of_day, end_of_day))
        except ValueError:
            pass
    
    tasks = query.all()
    employees = Employee.query.all()
    
    return render_template(
        "tasks.html", 
        tasks=tasks, 
        employees=employees,
        time_filter=time_filter,
        custom_date=custom_date
    )

@tasks_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        task = Task(
            company_name=request.form.get("company_name"),
            service_type=request.form.get("service_type"),
            employee_id=request.form.get("employee_id"),
            is_done=False
        )
        
        db.session.add(task)
        db.session.commit()
        flash("تم إضافة المهمة بنجاح", "success")
        return redirect(url_for("tasks.index"))
    
    employees = Employee.query.all()
    return render_template("add_task.html", employees=employees)

@tasks_bp.route("/edit/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit(task_id):
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))

    task = Task.query.get_or_404(task_id)
    
    if request.method == "POST":
        task.company_name = request.form.get("company_name")
        task.service_type = request.form.get("service_type")
        task.employee_id = request.form.get("employee_id")
        
        # Handle task completion
        is_done = request.form.get("is_done") == "on"
        if is_done and not task.is_done:
            task.completion_date = datetime.utcnow()
        elif not is_done and task.is_done:
            task.completion_date = None
        
        task.is_done = is_done
        
        db.session.commit()
        flash("تم تحديث المهمة بنجاح", "success")
        return redirect(url_for("tasks.index"))
    
    employees = Employee.query.all()
    return render_template("edit_task.html", task=task, employees=employees)

@tasks_bp.route("/delete/<int:task_id>")
@login_required
def delete(task_id):
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))

    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash("تم حذف المهمة بنجاح", "success")
    return redirect(url_for("tasks.index"))

@tasks_bp.route("/toggle/<int:task_id>")
@login_required
def toggle_completion(task_id):
    task = Task.query.get_or_404(task_id)
    if "employee_id" in session and task.employee_id != session["employee_id"]:
        flash("ليس لديك صلاحية تعديل هذه المهمة.", "danger")
        return redirect(url_for("tasks.employee_tasks"))

    task.is_done = not task.is_done
    
    if task.is_done:
        task.completion_date = datetime.utcnow()
    else:
        task.completion_date = None
    
    db.session.commit()
    
    status = "مكتملة" if task.is_done else "غير مكتملة"
    flash(f"تم تحديث حالة المهمة إلى {status}", "success")
    
    # Redirect based on user type
    if "admin_id" in session:
        return redirect(url_for("tasks.index"))
    else:
        return redirect(url_for("tasks.employee_tasks"))

@tasks_bp.route("/employee_tasks")
@login_required
def employee_tasks():
    if "employee_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))

    employee_id = session["employee_id"]
    
    # الحصول على معاملات الفلترة
    time_filter = request.args.get("time_filter", "all", type=str)
    custom_date = request.args.get("custom_date", "", type=str)
    
    # بناء الاستعلام مع الترتيب من الجديد للقديم
    query = Task.query.filter_by(employee_id=employee_id).order_by(Task.created_at.desc())
    
    # تطبيق الفلاتر الزمنية
    now = datetime.utcnow()
    today = date.today()
    
    if time_filter == "today":
        # اليوم
        start_of_day = datetime.combine(today, datetime.min.time())
        query = query.filter(Task.created_at >= start_of_day)
    
    elif time_filter == "this_week":
        # هذا الأسبوع (آخر 7 أيام)
        one_week_ago = now - timedelta(days=7)
        query = query.filter(Task.created_at >= one_week_ago)
    
    elif time_filter == "this_month":
        # هذا الشهر (آخر 30 يوم)
        one_month_ago = now - timedelta(days=30)
        query = query.filter(Task.created_at >= one_month_ago)
    
    elif custom_date:
        # تاريخ مخصص
        try:
            custom_date_obj = datetime.strptime(custom_date, "%Y-%m-%d").date()
            start_of_day = datetime.combine(custom_date_obj, datetime.min.time())
            end_of_day = datetime.combine(custom_date_obj, datetime.max.time())
            query = query.filter(Task.created_at.between(start_of_day, end_of_day))
        except ValueError:
            pass
    
    assigned_tasks = query.all()
    return render_template(
        "tasks.html", 
        tasks=assigned_tasks, 
        employee_view=True,
        time_filter=time_filter,
        custom_date=custom_date
    )