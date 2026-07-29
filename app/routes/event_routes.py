import requests
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app import db
from app.models.event import Event
from app.models.booking import Booking
from app.schemas.event_schema import EventSchema, EventRequestSchema, EventApprovalSchema
from app.utils.decorators import role_required
from app.utils.audit_utils import log_action
from datetime import datetime

event_bp = Blueprint('events', __name__)

def update_expired_events():
    today = datetime.utcnow().strftime('%Y-%m-%d')
    events = Event.query.filter(Event.date < today, Event.status == 'upcoming').all()
    for e in events:
        e.status = 'completed'
    if events:
        db.session.commit()

@event_bp.route('', methods=['GET'])
@jwt_required()
def get_events():
    """
    List All Public Events
    ---
    tags:
      - Events
    security:
      - Bearer: []
    responses:
      200:
        description: List of public (non-private) events
      401:
        description: Missing or invalid JWT token
    """
    update_expired_events()
    events = Event.query.filter(
        Event.status.in_(['upcoming', 'completed', 'full']),
        Event.is_private == False
    ).all()
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
    """
    Create a New Event
    ---
    tags:
      - Events
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - date
            - venue
            - capacity
            - price
          properties:
            name:
              type: string
              example: Tech Conference 2026
            date:
              type: string
              example: "2026-08-15"
            venue:
              type: string
              example: Expo Center, Bahawalpur
            capacity:
              type: integer
              example: 150
            price:
              type: number
              example: 2000
            description:
              type: string
              example: Annual tech meetup
    responses:
      201:
        description: Event created successfully
      400:
        description: Validation error
      403:
        description: Only Super Admin can create events
    """
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
    log_action(current_user_id, "event_created", f"Event '{new_event.name}' (ID {new_event.id}) created")
    return jsonify({"message": "Event created successfully", "id": new_event.id}), 201

@event_bp.route('/request', methods=['POST'])
@role_required('user')
def request_event():
    try:
        data = EventRequestSchema().load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    current_user_id = get_jwt_identity()
    new_event = Event(
        name=data['name'], date=data['date'], venue=data['venue'],
        capacity=data['capacity'], description=data.get('description'),
        status='pending', requested_by=current_user_id, price=None,
        is_private=True
    )
    db.session.add(new_event)
    db.session.commit()
    return jsonify({"message": "Event request submitted for approval", "id": new_event.id}), 201
@event_bp.route('/<int:event_id>/approve', methods=['PUT'])
@role_required('admin', 'super_admin')
def approve_event(event_id):
    e = Event.query.get_or_404(event_id)
    try:
        data = EventApprovalSchema().load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    current_user_id = get_jwt_identity()
    e.price = data['price']
    e.status = 'upcoming'
    e.admin_id = current_user_id
    db.session.commit()

    # Automatically book this private event for the requesting user
    new_booking = Booking(user_id=e.requested_by, event_id=e.id, status='registered')
    db.session.add(new_booking)
    db.session.commit()

    return jsonify({"message": "Event approved, priced, and booked for the requester"}), 200

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
    log_action(current_user_id, "event_updated", f"Event ID {e.id} updated")
    return jsonify({"message": "Event updated successfully"}), 200


@event_bp.route('/<int:event_id>', methods=['DELETE'])
@role_required('admin', 'super_admin')
def delete_event(event_id):
    """
    Delete an Event
    ---
    tags:
      - Events
    security:
      - Bearer: []
    parameters:
      - in: path
        name: event_id
        type: integer
        required: true
    responses:
      200:
        description: Event deleted successfully
      400:
        description: Cannot delete an event with existing bookings
      403:
        description: Not authorized to delete this event
      404:
        description: Event not found
    """
    e = Event.query.get_or_404(event_id)
    claims = get_jwt()
    current_user_id = get_jwt_identity()

    if claims.get('role') == 'admin' and str(e.admin_id) != str(current_user_id):
        return jsonify({"error": "You can only delete your own events"}), 403

    existing_bookings = Booking.query.filter_by(event_id=event_id).count()
    if existing_bookings > 0:
        return jsonify({"error": "Cannot delete an event with existing bookings"}), 400
    
    db.session.delete(e)
    event_name = e.name
    event_id = e.id
    db.session.delete(e)
    db.session.commit()
    log_action(current_user_id, "event_deleted", f"Event '{event_name}' (ID {event_id}) deleted")
    db.session.commit()
    return jsonify({"message": "Event deleted successfully"}), 200

@event_bp.route('/<int:event_id>/cancel', methods=['PUT'])
@role_required('super_admin')
def cancel_event(event_id):
    e = Event.query.get_or_404(event_id)
    e.status = 'cancelled'
    db.session.commit()
    log_action(get_jwt_identity(), "event_cancelled", f"Event '{e.name}' (ID {e.id}) cancelled")
    return jsonify({"message": "Event cancelled successfully"}), 200

def interpret_weather_code(code):
    mapping = {
        0: ("Clear sky", False),
        1: ("Mainly clear", False),
        2: ("Partly cloudy", False),
        3: ("Overcast", False),
        45: ("Fog", False),
        48: ("Depositing rime fog", False),
        51: ("Light drizzle", False),
        61: ("Slight rain", False),
        63: ("Moderate rain", True),
        65: ("Heavy rain", True),
        71: ("Slight snow", True),
        75: ("Heavy snow", True),
        80: ("Rain showers", True),
        95: ("Thunderstorm", True),
        99: ("Thunderstorm with hail", True),
    }
    return mapping.get(code, ("Unknown", False))


@event_bp.route('/<int:event_id>/weather', methods=['GET'])
@jwt_required()
def get_event_weather(event_id):
    e = Event.query.get_or_404(event_id)

    try:
        # Step A: Venue address ko coordinates mein convert karo (Nominatim)
        geo_resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": e.venue, "format": "json", "limit": 1},
            headers={"User-Agent": "EventManagementSystem/1.0"},
            timeout=10
        )
        geo_data = geo_resp.json()

        if not geo_data:
            return jsonify({"error": "Could not resolve venue location for weather"}), 404

        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]

        # Step B: Un coordinates se weather mangwao (Open-Meteo)
        weather_resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weathercode,windspeed_10m",
                "daily": "weathercode,temperature_2m_max,temperature_2m_min",
                "timezone": "auto"
            },
            timeout=10
        )
        weather_data = weather_resp.json()

        current = weather_data.get("current", {})
        daily = weather_data.get("daily", {})

        code = current.get("weathercode")
        description, severe = interpret_weather_code(code)

        return jsonify({
            "venue": e.venue,
            "current_temp": current.get("temperature_2m"),
            "wind_speed": current.get("windspeed_10m"),
            "condition": description,
            "severe_warning": severe,
            "forecast_max_temp": daily.get("temperature_2m_max", [None])[0],
            "forecast_min_temp": daily.get("temperature_2m_min", [None])[0]
        }), 200

    except Exception:
        return jsonify({"error": "Failed to fetch weather data"}), 500