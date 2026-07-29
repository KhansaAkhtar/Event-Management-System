from app import db
from datetime import datetime

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)      # e.g. 'login', 'event_created'
    details = db.Column(db.String(500))                     # e.g. "Event ID 5 created"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)