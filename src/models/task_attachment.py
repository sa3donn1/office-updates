from datetime import datetime
from src.models.user import db


class TaskAttachment(db.Model):
    __tablename__ = 'task_attachments'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    # relationships (optional convenience)
    task = db.relationship('Task', backref=db.backref('attachments', lazy='dynamic'))
    employee = db.relationship('Employee')

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'employee_id': self.employee_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'notes': self.notes
        }
