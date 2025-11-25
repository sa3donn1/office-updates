from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, current_app
from datetime import datetime
from sqlalchemy import func
from src.routes.auth import login_required
from src.models.user import db
from src.models.power_of_attorney import PowerOfAttorney
from src.models.power_of_attorney_movement import PowerOfAttorneyMovement
from src.models.employee import Employee   # لو عندك موديل الموظف في ملف تاني
import io
import traceback
import pandas as pd
from openpyxl import Workbook

power_of_attorney_bp = Blueprint('power_of_attorney', __name__)


# -----------------------------------------------------
#                فهرس التوكيلات
# -----------------------------------------------------
@power_of_attorney_bp.route("/")
@login_required
def index():
    """عرض فهرس التوكيلات"""

    search_query = request.args.get('search', '').strip()

    query = PowerOfAttorney.query.order_by(PowerOfAttorney.sequence_number)

    # بحث بالاسم أو الشركة
    if search_query:
        query = query.filter(
            db.or_(
                PowerOfAttorney.name.ilike(f'%{search_query}%'),
                PowerOfAttorney.company_name.ilike(f'%{search_query}%')
            )
        )

    power_of_attorneys = query.all()

    # آخر حركة لكل توكيل
    latest_movements = {
        poa.id: PowerOfAttorneyMovement.query
            .filter_by(power_id=poa.id)
            .order_by(PowerOfAttorneyMovement.taken_at.desc())
            .first()
        for poa in power_of_attorneys
    }

    employee_view = "employee_id" in session  # لو المستخدم موظف

    return render_template(
        "power_of_attorney_index.html",
        power_of_attorneys=power_of_attorneys,
        latest_movements=latest_movements,
        employees=Employee.query.all(),
        employee_view=employee_view,
        search_query=search_query
    )


# -----------------------------------------------------
#               إضافة التوكيل
# -----------------------------------------------------
@power_of_attorney_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_power_of_attorney():
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        sequence_number = request.form["sequence_number"]
        name = request.form["name"]
        company_name = request.form.get("company_name", "").strip()
        has_power_of_attorney = 'has_power_of_attorney' in request.form
        notes = request.form.get("notes", "").strip()

        # التأكد من رقم التسلسل
        existing_poa = PowerOfAttorney.query.filter_by(sequence_number=sequence_number).first()
        if existing_poa:
            flash("رقم التسلسل موجود بالفعل!", "danger")
            return render_template("add_power_of_attorney.html")

        new_poa = PowerOfAttorney(
            sequence_number=sequence_number,
            name=name,
            company_name=company_name or None,
            has_power_of_attorney=has_power_of_attorney,
            notes=notes or None
        )

        db.session.add(new_poa)
        db.session.commit()
        flash("تم إضافة التوكيل بنجاح!", "success")
        return redirect(url_for("power_of_attorney.index"))

    max_sequence = db.session.query(func.max(PowerOfAttorney.sequence_number)).scalar()
    next_sequence = (max_sequence + 1) if max_sequence else 1

    return render_template("add_power_of_attorney.html", next_sequence=next_sequence)


# -----------------------------------------------------
#               تعديل التوكيل
# -----------------------------------------------------
@power_of_attorney_bp.route("/edit/<int:poa_id>", methods=["GET", "POST"])
@login_required
def edit_power_of_attorney(poa_id):
    if "admin_id" not in session:
        flash("ليس لديك صلاحية الوصول.", "danger")
        return redirect(url_for("auth.login"))

    poa = PowerOfAttorney.query.get_or_404(poa_id)

    if request.method == "POST":
        sequence_number = request.form["sequence_number"]
        name = request.form["name"]
        company_name = request.form.get("company_name", "").strip()
        has_power_of_attorney = 'has_power_of_attorney' in request.form
        notes = request.form.get("notes", "").strip()

        # منع تكرار رقم التسلسل
        existing_poa = PowerOfAttorney.query.filter_by(sequence_number=sequence_number)\
                                           .filter(PowerOfAttorney.id != poa_id)\
                                           .first()

        if existing_poa:
            flash("رقم التسلسل موجود بالفعل!", "danger")
            return render_template("edit_power_of_attorney.html", poa=poa)

        poa.sequence_number = sequence_number
        poa.name = name
        poa.company_name = company_name or None
        poa.has_power_of_attorney = has_power_of_attorney
        poa.notes = notes or None

        db.session.commit()
        flash("تم تعديل التوكيل بنجاح!", "success")
        return redirect(url_for("power_of_attorney.index"))

    return render_template("edit_power_of_attorney.html", poa=poa)


# -----------------------------------------------------
#                حذف التوكيل
# -----------------------------------------------------
@power_of_attorney_bp.route("/delete/<int:poa_id>", methods=["POST"])
@login_required
def delete_power_of_attorney(poa_id):
    if "admin_id" not in session:
        flash("ليس لديك صلاحية.", "danger")
        return redirect(url_for("auth.login"))

    poa = PowerOfAttorney.query.get_or_404(poa_id)

    db.session.delete(poa)
    db.session.commit()

    flash("تم حذف التوكيل.", "success")
    return redirect(url_for("power_of_attorney.index"))


# -----------------------------------------------------
#            تسليم توكيل لموظف
# -----------------------------------------------------
@power_of_attorney_bp.route("/assign", methods=["POST"])
@login_required
def assign_power_of_attorney():
    if "admin_id" not in session:
        flash("غير مسموح.", "danger")
        return redirect(url_for("power_of_attorney.index"))

    power_id = request.form.get("power_id")
    employee_id = request.form.get("employee_id")
    notes = request.form.get("notes")

    # التأكد إن التوكيل مش مع حد
    open_movement = PowerOfAttorneyMovement.query \
        .filter_by(power_id=power_id, returned_at=None).first()

    if open_movement:
        flash("هذا التوكيل بالفعل مع موظف آخر.", "danger")
        return redirect(url_for("power_of_attorney.index"))

    move = PowerOfAttorneyMovement(
        power_id=power_id,
        employee_id=employee_id,
        notes=notes
    )

    db.session.add(move)
    db.session.commit()

    flash("تم تسليم التوكيل للموظف!", "success")
    return redirect(url_for("power_of_attorney.index"))


# -----------------------------------------------------
#            استلام توكيل من موظف
# -----------------------------------------------------
@power_of_attorney_bp.route("/return", methods=["POST"])
@login_required
def return_power_of_attorney():
    if "admin_id" not in session:
        flash("غير مسموح.", "danger")
        return redirect(url_for("power_of_attorney.index"))

    power_id = request.form.get("power_id")
    notes = request.form.get("notes")

    open_movement = PowerOfAttorneyMovement.query \
        .filter_by(power_id=power_id, returned_at=None).first()

    if not open_movement:
        flash("التوكيل غير مسلّم لموظف.", "danger")
        return redirect(url_for("power_of_attorney.index"))

    open_movement.returned_at = datetime.utcnow()
    if notes:
        open_movement.notes = (open_movement.notes or "") + "\n" + notes

    db.session.commit()

    flash("تم استلام التوكيل بنجاح!", "success")
    return redirect(url_for("power_of_attorney.index"))


# -----------------------------------------------------
#               سجل حركة التوكيل
# -----------------------------------------------------
@power_of_attorney_bp.route("/history/<int:poa_id>")
@login_required
def power_history(poa_id):
    poa = PowerOfAttorney.query.get_or_404(poa_id)

    movements = PowerOfAttorneyMovement.query \
        .filter_by(power_id=poa.id) \
        .order_by(PowerOfAttorneyMovement.taken_at.desc()) \
        .all()

    return render_template(
        "power_of_attorney_history.html",
        poa=poa,
        movements=movements
    )


# -----------------------------------------------------
#            APIs (لو عايز تستخدمها)
# -----------------------------------------------------
@power_of_attorney_bp.route("/api/all")
@login_required
def get_all_power_of_attorneys_api():
    power_of_attorneys = PowerOfAttorney.query.order_by(PowerOfAttorney.sequence_number).all()
    return jsonify([poa.to_dict() for poa in power_of_attorneys])


@power_of_attorney_bp.route("/api/stats")
@login_required
def get_power_of_attorney_stats_api():
    total_count = PowerOfAttorney.query.count()
    available_count = PowerOfAttorney.query.filter_by(has_power_of_attorney=True).count()
    unavailable_count = total_count - available_count

    return jsonify({
        'total': total_count,
        'available': available_count,
        'unavailable': unavailable_count
    })


# API: history data as JSON for a given poa
@power_of_attorney_bp.route('/api/history/<int:poa_id>')
@login_required
def get_history_api(poa_id):
    poa = PowerOfAttorney.query.get_or_404(poa_id)
    movements = PowerOfAttorneyMovement.query.filter_by(power_id=poa.id).order_by(PowerOfAttorneyMovement.taken_at.desc()).all()

    out = []
    for m in movements:
        employee = None
        try:
            employee = getattr(m, 'employee') if hasattr(m, 'employee') else None
        except Exception:
            employee = None
        out.append({
            'id': m.id,
            'employee_id': m.employee_id,
            'employee_name': employee.name if employee else None,
            'taken_at': m.taken_at.strftime('%Y-%m-%d %H:%M') if m.taken_at else None,
            'returned_at': m.returned_at.strftime('%Y-%m-%d %H:%M') if m.returned_at else None,
            'notes': m.notes
        })

    return jsonify({'movements': out})


# ----------------------------
# تنزيل ملف Excel كامل بالتوكيلات
# ----------------------------
@power_of_attorney_bp.route('/template')
@login_required
def download_template():
    """تنزيل ملف Excel يحتوي على كل التوكيلات بدلاً من نموذج فارغ"""
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "delegations"

        headers = ["serial", "name", "company", "status", "notes"]
        ws.append(headers)

        # جلب السجلات مرتبة حسب رقم التسلسل
        records = PowerOfAttorney.query.order_by(PowerOfAttorney.sequence_number.asc()).all()

        for r in records:
            status_val = "موجود" if getattr(r, 'has_power_of_attorney', False) else "غير موجود"
            ws.append([
                getattr(r, 'sequence_number', None),
                getattr(r, 'name', ''),
                getattr(r, 'company_name', ''),
                status_val,
                getattr(r, 'notes', '')
            ])

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)

        return send_file(
            stream,
            as_attachment=True,
            download_name="power_of_attorney_full.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        current_app.logger.error('Template download error: %s', traceback.format_exc())
        return jsonify({'error': 'فشل تحميل الملف: ' + str(e)}), 500


# ----------------------------
# استيراد توكيلات من Excel
# ----------------------------
@power_of_attorney_bp.route('/import-delegations', methods=['POST'])
@login_required
def import_delegations():
    """استيراد توكيلات من ملف Excel"""
    # فقط للأدمن
    if 'admin_id' not in session:
        return jsonify({'error': 'غير مسموح'}), 403

    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'لم يتم إرسال ملف'}), 400

    filename = getattr(file, 'filename', '')
    allowed = ('.xls', '.xlsx')
    if not any(filename.lower().endswith(ext) for ext in allowed):
        return jsonify({'error': 'الملف يجب أن يكون Excel (.xls أو .xlsx)'}), 400

    errors = []
    added = 0

    try:
        # اقرأ الملف
        df = pd.read_excel(file, engine='openpyxl')
        # normalize column names to lower
        df.columns = [str(c).strip().lower() for c in df.columns]

        required = ['serial', 'name']

        for idx, row in df.iterrows():
            rowno = idx + 2  # assume header row at 1
            try:
                # تحقق الحقول الأساسية موجودة
                missing_cols = [col for col in required if col not in df.columns]
                if missing_cols:
                    if idx == 0:  # report only once
                        errors.append(f'الملف يفقد الأعمدة المطلوبة: {", ".join(missing_cols)}')
                    break

                serial = row.get('serial')
                name = row.get('name')
                company = row.get('company') if 'company' in df.columns else None
                status = str(row.get('status')) if 'status' in df.columns else ''
                notes = row.get('notes') if 'notes' in df.columns else None

                # تحقق من القيم الفارغة للحقول الأساسية
                if pd.isna(serial) or pd.isna(name) or str(serial).strip() == '' or str(name).strip() == '':
                    errors.append(f'الصف {rowno}: الحقول serial أو name فارغة - تم التخطي')
                    continue

                # حاول تحويل serial إلى رقم متسلسل إن أمكن
                try:
                    seq = int(float(serial))
                except (ValueError, TypeError):
                    seq = str(serial).strip()

                # تحقق من وجود نفس رقم التسلسل
                exists = PowerOfAttorney.query.filter_by(sequence_number=seq).first()
                if exists:
                    errors.append(f'الصف {rowno}: رقم التسلسل "{serial}" موجود مسبقاً - تم التخطي')
                    continue

                # map status بسيط -> boolean has_power_of_attorney
                s = (status or '').strip().lower()
                has_poa = s in ('true', '1', 'yes', 'available', 'returned', 'راجع', 'موجود')

                new_poa = PowerOfAttorney(
                    sequence_number=seq,
                    name=str(name).strip(),
                    company_name=str(company).strip() if company and not pd.isna(company) else None,
                    has_power_of_attorney=has_poa,
                    notes=str(notes).strip() if notes and not pd.isna(notes) else None
                )
                db.session.add(new_poa)
                added += 1
            except Exception as e_row:
                errors.append(f'الصف {rowno}: {str(e_row)}')
                current_app.logger.error('Import row error: %s', traceback.format_exc())

        # بعد المرور على الصفوف، اتمام التغييرات
        if added > 0:
            try:
                db.session.commit()
            except Exception as e_commit:
                db.session.rollback()
                return jsonify({'error': 'فشل حفظ البيانات: ' + str(e_commit)}), 500
        else:
            db.session.rollback()

    except Exception as e:
        current_app.logger.error('Import error: %s', traceback.format_exc())
        return jsonify({'error': 'فشل قراءة ملف Excel: ' + str(e)}), 400

    return jsonify({'added': added, 'errors': errors})