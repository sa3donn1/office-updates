from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from src.routes.auth import login_required
from src.models.employee import Employee
from src.models.client import Client
from src.models.user import db

employees_bp = Blueprint("employees", __name__)

@employees_bp.route("/")
@login_required
def index():
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))
    employees = Employee.query.all()
    return render_template("employees.html", employees=employees)

@employees_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        employee = Employee(
            employee_id=request.form.get("employee_id"),
            name=request.form.get("name"),
            username=request.form.get("username")
        )
        
        # Set password if provided
        password = request.form.get("password")
        if password:
            employee.set_password(password)
        
        db.session.add(employee)
        db.session.commit()
        flash("تم إضافة الموظف بنجاح", "success")
        return redirect(url_for("employees.index"))
    
    return render_template("add_employee.html")

@employees_bp.route("/edit/<int:employee_id>", methods=["GET", "POST"])
@login_required
def edit(employee_id):
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))

    employee = Employee.query.get_or_404(employee_id)
    
    if request.method == "POST":
        employee.employee_id = request.form.get("employee_id")
        employee.name = request.form.get("name")
        employee.username = request.form.get("username")
        
        # Update password if provided
        password = request.form.get("password")
        if password:
            employee.set_password(password)
        
        db.session.commit()
        flash("تم تحديث بيانات الموظف بنجاح", "success")
        return redirect(url_for("employees.index"))
    
    return render_template("edit_employee.html", employee=employee)

@employees_bp.route("/delete/<int:employee_id>")
@login_required
def delete(employee_id):
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))

    employee = Employee.query.get_or_404(employee_id)
    
    # Check if employee has assigned clients
    if employee.clients:
        flash("لا يمكن حذف الموظف لأنه مسؤول عن عملاء", "error")
        return redirect(url_for("employees.index"))
    
    db.session.delete(employee)
    db.session.commit()
    flash("تم حذف الموظف بنجاح", "success")
    return redirect(url_for("employees.index"))

@employees_bp.route("/view/<int:employee_id>")
@login_required
def view(employee_id):
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))

    employee = Employee.query.get_or_404(employee_id)
    clients = Client.query.filter_by(employee_id=employee_id).all()
    return render_template("view_employee.html", employee=employee, clients=clients)




