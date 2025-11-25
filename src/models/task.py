from src.models.user import db
from datetime import datetime

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(100), nullable=False)
    is_done = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key to employee
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    
    def __repr__(self):
        return f'<Task {self.company_name} - {self.service_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'service_type': self.service_type,
            'is_done': self.is_done,
            'completion_date': self.completion_date.strftime('%Y-%m-%d') if self.completion_date else '',
            'responsible_employee': self.responsible_employee.name if self.responsible_employee else 'غير محدد',
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }