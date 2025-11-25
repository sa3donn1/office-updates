from src.models.user import db
from datetime import datetime

class PowerOfAttorney(db.Model):
    """
    نموذج فهرس التوكيلات - جدول مستقل لتتبع التوكيلات في المكتب
    """
    __tablename__ = 'power_of_attorney_index'
    
    id = db.Column(db.Integer, primary_key=True)
    sequence_number = db.Column(db.Integer, nullable=False, unique=True)  # رقم التسلسل
    name = db.Column(db.String(200), nullable=False)  # الاسم
    company_name = db.Column(db.String(200), nullable=True)  # اسم الشركة (اختياري)
    has_power_of_attorney = db.Column(db.Boolean, default=False, nullable=False)  # التوكيل موجود أم لا
    notes = db.Column(db.Text, nullable=True)  # ملاحظات إضافية
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # تاريخ الإضافة
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)  # تاريخ آخر تعديل
    
    def __repr__(self):
        return f'<PowerOfAttorney {self.sequence_number}: {self.name}>'
    
    def to_dict(self):
        """تحويل الكائن إلى قاموس للاستخدام مع JSON"""
        return {
            'id': self.id,
            'sequence_number': self.sequence_number,
            'name': self.name,
            'company_name': self.company_name,
            'has_power_of_attorney': self.has_power_of_attorney,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

