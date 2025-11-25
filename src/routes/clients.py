import shutil
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, current_app, jsonify
from src.models.client import Client, Document
from src.models.client_email import ClientEmail
from src.models.employee import Employee
from src.routes.auth import login_required
from src.models.user import db
import os
from werkzeug.utils import secure_filename

clients_bp = Blueprint('clients', __name__)

@clients_bp.route("/")
@login_required
def index():
    # Get filter parameters from URL
    client_type_filter = request.args.get('type', 'all')
    search_query = request.args.get('search', '').strip()
    
    # Start with base query
    query = Client.query
    
    # Apply type filter
    if client_type_filter == 'individual':
        query = query.filter_by(client_type='individual')
    elif client_type_filter == 'company':
        query = query.filter_by(client_type='company')
    
    # Apply search filter if search query exists
    if search_query:
        query = query.filter(Client.name.ilike(f'%{search_query}%'))
    
    clients = query.all()
    
    # Check if user is employee to set employee_view flag
    employee_view = "employee_id" in session
    return render_template("clients.html", clients=clients, employee_view=employee_view, 
                         current_filter=client_type_filter, search_query=search_query)

@clients_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_client():
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))

    employees = Employee.query.all()
    if request.method == "POST":
        name = request.form["name"]
        client_type = request.form["client_type"]
        platform_registration_number = request.form["platform_registration_number"]
        password = request.form["password"]
        tax_office = request.form["tax_office"]
        national_id = request.form["national_id"]
        tax_registration_number = request.form.get("tax_registration_number", "")
        declaration_status = request.form["declaration_status"]
        employee_id = request.form.get("employee_id")

        new_client = Client(
            name=name,
            client_type=client_type,
            platform_registration_number=platform_registration_number,
            password=password,
            tax_office=tax_office,
            national_id=national_id,
            tax_registration_number=tax_registration_number,
            declaration_status=declaration_status,
            employee_id=employee_id if employee_id else None
        )
        db.session.add(new_client)
        db.session.commit()

        flash("تم إضافة العميل بنجاح!", "success")
        return redirect(url_for("clients.index"))
    return render_template("add_client.html", employees=employees)
@clients_bp.route("/edit/<int:client_id>", methods=["GET", "POST"])
@login_required
def edit_client(client_id):
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))

    client = Client.query.get_or_404(client_id)
    employees = Employee.query.all()
    if request.method == "POST":
        client.name = request.form["name"]
        client.client_type = request.form["client_type"]
        client.platform_registration_number = request.form["platform_registration_number"]
        client.password = request.form["password"]
        client.tax_office = request.form["tax_office"]
        client.national_id = request.form["national_id"]
        client.tax_registration_number = request.form.get("tax_registration_number", "")
        client.declaration_status = request.form["declaration_status"]
        client.employee_id = request.form.get("employee_id") if request.form.get("employee_id") else None
        db.session.commit()
        flash("تم تحديث بيانات العميل بنجاح!", "success")
        return redirect(url_for("clients.index"))
    return render_template("edit_client.html", client=client, employees=employees)

@clients_bp.route("/delete/<int:client_id>", methods=["POST"])
@login_required
def delete_client(client_id):
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))

    client = Client.query.get_or_404(client_id)
    # Delete associated documents and folder
    for doc in client.documents:
        doc_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(client.id), doc.filename)
        if os.path.exists(doc_path):
            os.remove(doc_path)
        db.session.delete(doc)
    client_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(client.id))
    if os.path.exists(client_folder):
         shutil.rmtree(client_folder)

    db.session.delete(client)
    db.session.commit()
    flash("تم حذف العميل وجميع ملفاته بنجاح!", "success")
    return redirect(url_for("clients.index"))

@clients_bp.route("/files/<int:client_id>")
@login_required
def client_files(client_id):
    client = Client.query.get_or_404(client_id)
    # Allow all logged-in users (admin and employees) to view client files
    employee_view = "employee_id" in session
    return render_template("client_files.html", client=client, employee_view=employee_view)

@clients_bp.route("/upload_file/<int:client_id>", methods=["POST"])
@login_required
def upload_file(client_id):
    client = Client.query.get_or_404(client_id)
    if "employee_id" in session and client.employee_id != session["employee_id"]:
        flash("ليس لديك صلاحية رفع ملفات لهذا العميل.", "danger")
        return redirect(url_for("dashboard.employee_dashboard"))

    if "file" not in request.files:
        flash("لم يتم اختيار ملف!", "danger")
        return redirect(url_for("clients.client_files", client_id=client_id))

    file = request.files["file"]
    if file.filename == "":
        flash("لم يتم اختيار ملف!", "danger")
        return redirect(url_for("clients.client_files", client_id=client_id))

    if file:
        filename = secure_filename(file.filename)
        client_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(client.id))
        os.makedirs(client_folder, exist_ok=True)
        file_path = os.path.join(client_folder, filename)
        file.save(file_path)

        new_document = Document(
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            client_id=client.id
        )
        db.session.add(new_document)
        db.session.commit()
        flash("تم رفع الملف بنجاح!", "success")

    return redirect(url_for("clients.client_files", client_id=client_id))
@clients_bp.route("/download_file/<int:document_id>")
@login_required
def download_file(document_id):
    document = Document.query.get_or_404(document_id)
    client = document.client
    # Allow all logged-in users (admin and employees) to download client files
    return send_from_directory(os.path.join(current_app.config['UPLOAD_FOLDER'], str(client.id)), document.filename, as_attachment=True)

@clients_bp.route("/delete_file/<int:document_id>", methods=["POST"])
@login_required
def delete_file(document_id):
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))

    document = Document.query.get_or_404(document_id)
    client_id = document.client_id
    doc_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(client_id), document.filename)
    if os.path.exists(doc_path):
        os.remove(doc_path)
    db.session.delete(document)
    db.session.commit()
    flash("تم حذف الملف بنجاح!", "success")
    return redirect(url_for("clients.client_files", client_id=client_id))

@clients_bp.route("/employee_clients")
@login_required
def employee_clients():
    if "employee_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))

    employee_id = session["employee_id"]
    assigned_clients = Client.query.filter_by(employee_id=employee_id).all()
    return render_template("clients.html", clients=assigned_clients, employee_view=True)

# ==================== Client Email Management Routes ====================

@clients_bp.route("/emails/<int:client_id>")
@login_required
def client_emails(client_id):
    """عرض جميع الإيميلات الخاصة بعميل معين"""
    client = Client.query.get_or_404(client_id)
    emails = ClientEmail.query.filter_by(client_id=client_id).all()
    return render_template("client_emails.html", client=client, emails=emails)

@clients_bp.route("/emails/<int:client_id>/add", methods=["GET", "POST"])
@login_required
def add_client_email(client_id):
    """إضافة إيميل جديد لعميل"""
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))
    
    client = Client.query.get_or_404(client_id)
    
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        description = request.form.get("description", "")
        
        # التحقق من عدم تكرار الإيميل لنفس العميل
        existing_email = ClientEmail.query.filter_by(client_id=client_id, email=email).first()
        if existing_email:
            flash("هذا الإيميل موجود بالفعل لهذا العميل!", "danger")
            return render_template("add_client_email.html", client=client)
        
        new_email = ClientEmail(
            client_id=client_id,
            email=email,
            password=password,
            description=description
        )
        
        db.session.add(new_email)
        db.session.commit()
        flash("تم إضافة الإيميل بنجاح!", "success")
        return redirect(url_for("clients.client_emails", client_id=client_id))
    
    return render_template("add_client_email.html", client=client)

@clients_bp.route("/emails/edit/<int:email_id>", methods=["GET", "POST"])
@login_required
def edit_client_email(email_id):
    """تعديل إيميل عميل"""
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))
    
    email_obj = ClientEmail.query.get_or_404(email_id)
    client = email_obj.client
    
    if request.method == "POST":
        new_email = request.form["email"]
        password = request.form["password"]
        description = request.form.get("description", "")
        
        # التحقق من عدم تكرار الإيميل لنفس العميل (باستثناء الإيميل الحالي)
        existing_email = ClientEmail.query.filter_by(client_id=client.id, email=new_email).filter(ClientEmail.id != email_id).first()
        if existing_email:
            flash("هذا الإيميل موجود بالفعل لهذا العميل!", "danger")
            return render_template("edit_client_email.html", client=client, email=email_obj)
        
        email_obj.email = new_email
        email_obj.password = password
        email_obj.description = description
        
        db.session.commit()
        flash("تم تعديل الإيميل بنجاح!", "success")
        return redirect(url_for("clients.client_emails", client_id=client.id))
    
    return render_template("edit_client_email.html", client=client, email=email_obj)

@clients_bp.route("/emails/delete/<int:email_id>", methods=["POST"])
@login_required
def delete_client_email(email_id):
    """حذف إيميل عميل"""
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("auth.login"))
    
    email_obj = ClientEmail.query.get_or_404(email_id)
    client_id = email_obj.client_id
    
    db.session.delete(email_obj)
    db.session.commit()
    flash("تم حذف الإيميل بنجاح!", "success")
    return redirect(url_for("clients.client_emails", client_id=client_id))

@clients_bp.route("/api/emails/<int:client_id>")
@login_required
def get_client_emails_api(client_id):
    """API لجلب إيميلات العميل (للاستخدام مع AJAX)"""
    emails = ClientEmail.query.filter_by(client_id=client_id).all()
    return jsonify([email.to_dict() for email in emails])

