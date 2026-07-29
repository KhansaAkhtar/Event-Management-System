from app import db
from app.models.audit_log import AuditLog

def log_action(user_id, action, details=""):
    entry = AuditLog(user_id=user_id, action=action, details=details)
    db.session.add(entry)
    db.session.commit()