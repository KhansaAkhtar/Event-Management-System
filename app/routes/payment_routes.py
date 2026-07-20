from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app import db
from app.models.payment import Payment
from app.models.booking import Booking
from app.models.event import Event
from app.schemas.payment_schema import PaymentSchema, PaymentUpdateSchema
from app.utils.decorators import role_required

payment_bp = Blueprint('payments', __name__)

@payment_bp.route('', methods=['POST'])
@role_required('user')
def create_payment():
    try:
        data = PaymentSchema().load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    booking = Booking.query.get(data['booking_id'])
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    current_user_id = get_jwt_identity()
    if str(booking.user_id) != str(current_user_id):
        return jsonify({"error": "You can only pay for your own booking"}), 403
    if booking.status == 'cancelled':
        return jsonify({"error": "Cannot pay for a cancelled booking"}), 400
    existing_payment = Payment.query.filter_by(booking_id=data['booking_id']).filter(
        Payment.status.in_(['pending', 'paid'])
    ).first()

    if existing_payment:
        return jsonify({"error": "A payment for this booking already exists"}), 409
    new_payment = Payment(booking_id=data['booking_id'], amount=data['amount'])
    db.session.add(new_payment)
    db.session.commit()
    return jsonify({"message": "Payment created successfully", "id": new_payment.id}), 201


@payment_bp.route('/my', methods=['GET'])
@jwt_required()
def get_my_payments():
    current_user_id = get_jwt_identity()
    bookings = Booking.query.filter_by(user_id=current_user_id).all()
    booking_ids = [b.id for b in bookings]
    payments = Payment.query.filter(Payment.booking_id.in_(booking_ids)).all()
    result = [{
        "id": p.id, "booking_id": p.booking_id, "amount": p.amount,
        "status": p.status, "payment_date": p.payment_date.isoformat()
    } for p in payments]
    return jsonify(result), 200


@payment_bp.route('/event/<int:event_id>', methods=['GET'])
@role_required('admin', 'super_admin')
def get_event_payments(event_id):
    claims = get_jwt()
    current_user_id = get_jwt_identity()
    event = Event.query.get_or_404(event_id)

    if claims.get('role') == 'admin' and str(event.admin_id) != str(current_user_id):
        return jsonify({"error": "You can only view your own event's payments"}), 403

    bookings = Booking.query.filter_by(event_id=event_id).all()
    booking_ids = [b.id for b in bookings]
    payments = Payment.query.filter(Payment.booking_id.in_(booking_ids)).all()
    result = [{
        "id": p.id, "booking_id": p.booking_id, "amount": p.amount,
        "status": p.status, "payment_date": p.payment_date.isoformat()
    } for p in payments]
    return jsonify(result), 200


@payment_bp.route('/<int:payment_id>', methods=['PUT'])
@role_required('admin', 'super_admin')
def update_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    try:
        data = PaymentUpdateSchema().load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    payment.status = data['status']
    db.session.commit()
    return jsonify({"message": "Payment status updated successfully"}), 200