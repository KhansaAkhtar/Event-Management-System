from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from app import db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.utils.decorators import role_required

user_bp = Blueprint('users', __name__)

from app.models.audit_log import AuditLog

@user_bp.route('/audit-log', methods=['GET'])
@role_required('super_admin')
def get_audit_log():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    result = [{
        "id": l.id, "user_id": l.user_id, "action": l.action,
        "details": l.details, "timestamp": l.timestamp.isoformat()
    } for l in logs]
    return jsonify(result), 200


@user_bp.route('', methods=['GET'])
@role_required('super_admin')
def get_all_users():
    current_user_id = get_jwt_identity()
    users = User.query.filter(User.id != current_user_id).all()
    result = [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users]
    return jsonify(result), 200

@user_bp.route('/<int:user_id>/role', methods=['PUT'])
@role_required('super_admin')
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.get_json().get('role')
    if new_role not in ['admin', 'vendor', 'user', 'super_admin']:
        return jsonify({"error": "Invalid role"}), 400
    user.role = new_role
    db.session.commit()
    return jsonify({"message": "Role updated successfully"}), 200

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@role_required('super_admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200