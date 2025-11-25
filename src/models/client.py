from src.models.user import db
from datetime import datetime

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    client_type = db.Column(db.String(20), nullable=False)  # 'individual' or 'company'
    platform_registration_number = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    tax_office = db.Column(db.String(100), nullable=False)  # مأمورية
    national_id = db.Column(db.String(50), nullable=False)
    tax_registration_number = db.Column(db.String(50), nullable=True)  # رقم التسجيل الضريبي
    declaration_status = db.Column(db.String(50), default='pending')  # pending, completed, in_progress
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key to employee
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    # لا تضف أي علاقة هنا، العلاقة ستكون في Employee فقط

    # Relationship with documents
    documents = db.relationship('Document', backref='client', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Client {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'client_type': self.client_type,
            'platform_registration_number': self.platform_registration_number,
            'password': self.password,
            'tax_office': self.tax_office,
            'national_id': self.national_id,
            'tax_registration_number': self.tax_registration_number,
            'declaration_status': self.declaration_status,
            'employee': self.employee.name if self.employee else 'غير محدد',
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key to client
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'uploaded_at': self.uploaded_at.strftime('%Y-%m-%d %H:%M') if self.uploaded_at else ''
        }