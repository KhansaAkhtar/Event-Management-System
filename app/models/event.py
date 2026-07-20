from app import db

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    venue = db.Column(db.String(150), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500))
    status = db.Column(db.String(20), default='upcoming')
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0)      