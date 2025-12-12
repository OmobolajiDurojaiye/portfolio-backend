from app import db
from datetime import datetime

class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(10), nullable=False) # e.g., "Monday", "Tuesday"
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M')
        }

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(120), nullable=False)
    meeting_time = db.Column(db.DateTime, nullable=False)
    meeting_duration = db.Column(db.Integer, nullable=False) # in minutes
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Pending') # Pending, Confirmed, Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'client_name': self.client_name,
            'client_email': self.client_email,
            'meeting_time': self.meeting_time.isoformat(),
            'meeting_duration': self.meeting_duration,
            'notes': self.notes,
            'status': self.status
        }