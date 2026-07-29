from app import db
from datetime import datetime

class Waitlist(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
  joined_at = db.Column(db.DateTime, default=datetime.utcnow)
  status = db.Column(db.String(20), default='waiting')