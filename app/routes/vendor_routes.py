from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.vendor import Vendor
from app.models.event import Event
from app.schemas.vendor_schema import VendorSchema
from app.utils.decorators import role_required

vendor_bp = Blueprint('vendors', __name__)

@vendor_bp.route('', methods=['POST'])
@role_required('vendor')
def create_vendor():
    try:
        data = VendorSchema().load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    event = Event.query.get(data['event_id'])
    if not event:
        return jsonify({"error": "Event not found"}), 404

    current_user_id = get_jwt_identity()
    new_vendor = Vendor(
        user_id=current_user_id,
        service_type=data['service_type'],
        event_id=data['event_id']
    )
    db.session.add(new_vendor)
    db.session.commit()
    return jsonify({"message": "Vendor service added successfully", "id": new_vendor.id}), 201


@vendor_bp.route('/my', methods=['GET'])
@role_required('vendor')
def get_my_vendor_profile():
    current_user_id = get_jwt_identity()
    vendors = Vendor.query.filter_by(user_id=current_user_id).all()
    result = [{
        "id": v.id, "service_type": v.service_type, "event_id": v.event_id
    } for v in vendors]
    return jsonify(result), 200


@vendor_bp.route('/event/<int:event_id>', methods=['GET'])
@jwt_required()
def get_event_vendors(event_id):
    vendors = Vendor.query.filter_by(event_id=event_id).all()
    result = [{
        "id": v.id, "user_id": v.user_id, "service_type": v.service_type
    } for v in vendors]
    return jsonify(result), 200


@vendor_bp.route('/<int:vendor_id>', methods=['DELETE'])
@role_required('vendor')
def delete_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    current_user_id = get_jwt_identity()

    if str(vendor.user_id) != str(current_user_id):
        return jsonify({"error": "You can only delete your own service"}), 403

    db.session.delete(vendor)
    db.session.commit()
    return jsonify({"message": "Vendor service deleted successfully"}), 200