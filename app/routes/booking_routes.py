from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app import db
from app.models.booking import Booking
from app.models.event import Event
from app.models.payment import Payment
from app.schemas.booking_schema import BookingSchema
from app.utils.decorators import role_required
from app.utils.email_utils import send_email
from app.utils.audit_utils import log_action
from app.models.user import User
from app.models.waitlist import Waitlist
from app.models.booking_log import BookingAttemptLog

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

    # 1. Duplicate booking check
    existing_booking = Booking.query.filter_by(
        user_id=current_user_id, event_id=data['event_id']
    ).filter(Booking.status != 'cancelled').first()

    if existing_booking:
        db.session.add(BookingAttemptLog(user_id=current_user_id, event_id=data['event_id'], reason='duplicate_booking'))
        db.session.commit()
        return jsonify({"error": "You have already booked this event"}), 409

    # 2. Capacity check
    active_count = Booking.query.filter_by(event_id=data['event_id']).filter(Booking.status != 'cancelled').count()

    if active_count >= event.capacity:
        already_waiting = Waitlist.query.filter_by(user_id=current_user_id, event_id=data['event_id'], status='waiting').first()
        if already_waiting:
            db.session.add(BookingAttemptLog(user_id=current_user_id, event_id=data['event_id'], reason='already_on_waitlist'))
            db.session.commit()
            return jsonify({"error": "You are already on the waiting list for this event"}), 409

        db.session.add(Waitlist(user_id=current_user_id, event_id=data['event_id']))
        db.session.add(BookingAttemptLog(user_id=current_user_id, event_id=data['event_id'], reason='capacity_full'))
        event.status = 'full'
        db.session.commit()
        return jsonify({"message": "Event is full. You have been added to the waiting list."}), 202

    # 3. Normal booking
    new_booking = Booking(user_id=current_user_id, event_id=data['event_id'])
    db.session.add(new_booking)

    # 4. Agar ye booking capacity poori kar de, auto-close
    if active_count + 1 >= event.capacity:
        event.status = 'full'

    db.session.commit()
    log_action(current_user_id, "booking_created", f"Booked event ID {data['event_id']}, booking ID {new_booking.id}")
    user = User.query.get(current_user_id)
    send_email(
        subject=f"Booking Confirmed: {event.name}",
        recipients=[user.email],
        body=f"Hi {user.name},\n\nYour booking for '{event.name}' on {event.date} at {event.venue} is confirmed.\n\nSee you there!"
    )
    return jsonify({"message": "Booking created successfully", "id": new_booking.id}), 201


@booking_bp.route('/my', methods=['GET'])
@jwt_required()
def get_my_bookings():
    current_user_id = get_jwt_identity()
    bookings = Booking.query.filter_by(user_id=current_user_id).all()
    result = []
    for b in bookings:
        event = Event.query.get(b.event_id)
        payment = Payment.query.filter_by(booking_id=b.id).order_by(Payment.id.desc()).first()
        result.append({
            "id": b.id,
            "event_id": b.event_id,
            "event_name": event.name if event else "Unknown Event",
            "event_price": event.price if event else 0,
            "status": b.status,
            "payment_status": payment.status if payment else "not_paid",
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

@booking_bp.route('/waitlist/my', methods=['GET'])
@jwt_required()
def get_my_waitlist():
    current_user_id = get_jwt_identity()
    entries = Waitlist.query.filter_by(user_id=current_user_id, status='waiting').all()
    result = []
    for w in entries:
        event = Event.query.get(w.event_id)
        result.append({"id": w.id, "event_id": w.event_id, "event_name": event.name if event else "Unknown", "joined_at": w.joined_at.isoformat()})
    return jsonify(result), 200


@booking_bp.route('/rejected-log', methods=['GET'])
@role_required('super_admin')
def get_rejected_log():
    logs = BookingAttemptLog.query.order_by(BookingAttemptLog.attempted_at.desc()).all()
    result = [{"id": l.id, "user_id": l.user_id, "event_id": l.event_id, "reason": l.reason, "attempted_at": l.attempted_at.isoformat()} for l in logs]
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
    event = Event.query.get(booking.event_id)

    if event and event.status == 'full':
        event.status = 'upcoming'
        next_in_line = Waitlist.query.filter_by(event_id=event.id, status='waiting').order_by(Waitlist.joined_at.asc()).first()
        if next_in_line:
            db.session.add(Booking(user_id=next_in_line.user_id, event_id=event.id, status='registered'))
            next_in_line.status = 'promoted'
            event.status = 'full'

            promoted_user = User.query.get(next_in_line.user_id)
            send_email(
                subject=f"You're In! Spot Opened for {event.name}",
                recipients=[promoted_user.email],
                body=f"Hi {promoted_user.name},\n\nA spot opened up for '{event.name}', and you've been automatically booked from the waiting list!"
            )

    db.session.commit()
    log_action(current_user_id, "booking_cancelled", f"Booking ID {booking_id} cancelled")
    user = User.query.get(booking.user_id)
    event_obj = Event.query.get(booking.event_id)
    send_email(
        subject=f"Booking Cancelled: {event_obj.name if event_obj else 'Event'}",
        recipients=[user.email],
        body=f"Hi {user.name},\n\nYour booking for '{event_obj.name if event_obj else 'the event'}' has been cancelled."
    )
    return jsonify({"message": "Booking cancelled successfully"}), 200