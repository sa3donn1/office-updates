from src.models.user import db
from datetime import datetime, timedelta

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.now().date)
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationship with Employee
    employee = db.relationship("Employee", backref="attendance_records")
    
    # Add unique constraint to prevent multiple check-ins on same day
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'date', name='unique_employee_date'),
    )
    
    def get_working_hours(self):
        """Calculate working hours between check-in and check-out"""
        if self.check_in and self.check_out:
            duration = self.check_out - self.check_in
            hours = duration.total_seconds() / 3600
            return round(hours, 2)
        return None
    
    def __repr__(self):
        return f"<Attendance {self.employee.name} - {self.date}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "employee_name": self.employee.name,
            "date": self.date.strftime("%Y-%m-%d"),
            "check_in": self.check_in.strftime("%H:%M:%S") if self.check_in else None,
            "check_out": self.check_out.strftime("%H:%M:%S") if self.check_out else None,
            "working_hours": self.get_working_hours(),
            "notes": self.notes
        }
