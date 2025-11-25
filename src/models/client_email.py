from src.models.user import db
from datetime import datetime

class ClientEmail(db.Model):
    __tablename__ = 'client_emails'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=True)  # وصف نوع الإيميل (اختياري)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقة مع جدول العملاء
    client = db.relationship('Client', backref=db.backref('emails', lazy=True, cascade='all, delete-orphan'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'email': self.email,
            'password': self.password,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ClientEmail {self.email} for Client {self.client_id}>'

