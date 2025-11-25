from src.models.user import db
from datetime import datetime

class PowerOfAttorneyMovement(db.Model):
    __tablename__ = "power_of_attorney_movements"

    id = db.Column(db.Integer, primary_key=True)

    power_id = db.Column(db.Integer, db.ForeignKey("power_of_attorney_index.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"))

    taken_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    returned_at = db.Column(db.DateTime, nullable=True)

    notes = db.Column(db.Text, nullable=True)
    employee = db.relationship("Employee", backref="powers_movements")
    # علاقة بجدول التوكيلات
    power = db.relationship(
        "PowerOfAttorney",
        backref=db.backref("movements", lazy=True, cascade="all, delete")
    )