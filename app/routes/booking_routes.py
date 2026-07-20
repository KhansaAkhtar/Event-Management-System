from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app import db
from app.models.booking import Booking
from app.models.event import Event
from app.schemas.booking_schema import BookingSchema
from app.utils.decorators import role_required

booking_bp = Blueprint('bookings', __name__)

@booking_bp.route('', methods=['POST'])
@role_required('user')
def create_booking():
    try:
        data = BookingSchema().load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    event = Event.query.get(data['event_id'])
    if not event:
        return jsonify({"error": "Event not found"}), 404

    current_user_id = get_jwt_identity()
    existing_booking = Booking.query.filter_by(
        user_id=current_user_id,
        event_id=data['event_id']
    ).filter(Booking.status != 'cancelled').first()

    if existing_booking:
        return jsonify({"error": "You have already booked this event"}), 409
    new_booking = Booking(user_id=current_user_id, event_id=data['event_id'])
    db.session.add(new_booking)
    db.session.commit()
    return jsonify({"message": "Booking created successfully", "id": new_booking.id}), 201


@booking_bp.route('/my', methods=['GET'])
@jwt_required()
def get_my_bookings():
    current_user_id = get_jwt_identity()
    bookings = Booking.query.filter_by(user_id=current_user_id).all()
    result = []
    for b in bookings:
        event = Event.query.get(b.event_id)
        result.append({
            "id": b.id,
            "event_id": b.event_id,
            "event_name": event.name if event else "Unknown Event",
            "event_price": event.price if event else 0,
            "status": b.status,
            "booking_date": b.booking_date.isoformat()
        })
    return jsonify(result), 200


@booking_bp.route('/event/<int:event_id>', methods=['GET'])
@role_required('admin', 'super_admin')
def get_event_bookings(event_id):
    claims = get_jwt()
    current_user_id = get_jwt_identity()
    event = Event.query.get_or_404(event_id)

    if claims.get('role') == 'admin' and str(event.admin_id) != str(current_user_id):
        return jsonify({"error": "You can only view your own event's bookings"}), 403

    bookings = Booking.query.filter_by(event_id=event_id).all()
    result = [{
        "id": b.id, "user_id": b.user_id, "status": b.status,
        "booking_date": b.booking_date.isoformat()
    } for b in bookings]
    return jsonify(result), 200


@booking_bp.route('/<int:booking_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    if claims.get('role') == 'user' and str(booking.user_id) != str(current_user_id):
        return jsonify({"error": "You can only cancel your own booking"}), 403

    booking.status = 'cancelled'
    db.session.commit()
    return jsonify({"message": "Booking cancelled successfully"}), 200