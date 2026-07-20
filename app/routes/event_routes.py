from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app import db
from app.models.event import Event
from app.schemas.event_schema import EventSchema
from app.utils.decorators import role_required

event_bp = Blueprint('events', __name__)

@event_bp.route('', methods=['GET'])
@jwt_required()
def get_events():
    events = Event.query.all()
    result = [{
        "id": e.id, "name": e.name, "date": e.date, "venue": e.venue,
        "capacity": e.capacity, "price": e.price, "description": e.description,
        "status": e.status, "admin_id": e.admin_id
    } for e in events]
    return jsonify(result), 200


@event_bp.route('/<int:event_id>', methods=['GET'])
@jwt_required()
def get_event(event_id):
    e = Event.query.get_or_404(event_id)
    return jsonify({
        "id": e.id, "name": e.name, "date": e.date, "venue": e.venue,
        "capacity": e.capacity, "price": e.price, "description": e.description,
        "status": e.status, "admin_id": e.admin_id
    }), 200


@event_bp.route('', methods=['POST'])
@role_required('admin', 'super_admin')
def create_event():
    try:
        data = EventSchema().load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    current_user_id = get_jwt_identity()
    new_event = Event(
        name=data['name'], date=data['date'], venue=data['venue'],
        capacity=data['capacity'], price=data['price'], description=data.get('description'),
        status=data.get('status', 'upcoming'), admin_id=current_user_id
    )
    db.session.add(new_event)
    db.session.commit()
    return jsonify({"message": "Event created successfully", "id": new_event.id}), 201


@event_bp.route('/<int:event_id>', methods=['PUT'])
@role_required('admin', 'super_admin')
def update_event(event_id):
    e = Event.query.get_or_404(event_id)
    claims = get_jwt()
    current_user_id = get_jwt_identity()

    if claims.get('role') == 'admin' and str(e.admin_id) != str(current_user_id):
        return jsonify({"error": "You can only edit your own events"}), 403

    try:
        data = EventSchema(partial=True).load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    for key, value in data.items():
        setattr(e, key, value)
    db.session.commit()
    return jsonify({"message": "Event updated successfully"}), 200


@event_bp.route('/<int:event_id>', methods=['DELETE'])
@role_required('admin', 'super_admin')
def delete_event(event_id):
    e = Event.query.get_or_404(event_id)
    claims = get_jwt()
    current_user_id = get_jwt_identity()

    if claims.get('role') == 'admin' and str(e.admin_id) != str(current_user_id):
        return jsonify({"error": "You can only delete your own events"}), 403

    db.session.delete(e)
    db.session.commit()
    return jsonify({"message": "Event deleted successfully"}), 200