from app import db
from datetime import datetime

class ReminderLog(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
  sent_at = db.Column(db.DateTime, default=datetime.utcnow)
