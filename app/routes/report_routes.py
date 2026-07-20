from flask import Blueprint, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import openpyxl
from app.models.event import Event
from app.models.booking import Booking
from app.models.vendor import Vendor
from app.models.payment import Payment
from app.utils.decorators import role_required

report_bp = Blueprint('reports', __name__)


def check_event_access(event_id):
    """Shared helper: confirms admin owns the event, or user is super_admin"""
    claims = get_jwt()
    current_user_id = get_jwt_identity()
    event = Event.query.get_or_404(event_id)
    if claims.get('role') == 'admin' and str(event.admin_id) != str(current_user_id):
        return None
    return event


@report_bp.route('/revenue/<int:event_id>', methods=['GET'])
@role_required('admin', 'super_admin')
def revenue_report(event_id):
    event = check_event_access(event_id)
    if not event:
        return jsonify({"error": "Access denied"}), 403

    bookings = Booking.query.filter_by(event_id=event_id).all()
    booking_ids = [b.id for b in bookings]
    payments = Payment.query.filter(Payment.booking_id.in_(booking_ids), Payment.status == 'paid').all()
    total_revenue = sum(p.amount for p in payments)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(50, 750, f"Revenue Report - {event.name}")
    p.drawString(50, 720, f"Total Paid Payments: {len(payments)}")
    p.drawString(50, 700, f"Total Revenue: {total_revenue}")
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"revenue_report_event_{event_id}.pdf", mimetype='application/pdf')


@report_bp.route('/attendance/<int:event_id>', methods=['GET'])
@role_required('admin', 'super_admin')
def attendance_report(event_id):
    event = check_event_access(event_id)
    if not event:
        return jsonify({"error": "Access denied"}), 403

    bookings = Booking.query.filter_by(event_id=event_id).all()

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    p.drawString(50, y, f"Attendance Report - {event.name}")
    y -= 30
    for b in bookings:
        p.drawString(50, y, f"User ID: {b.user_id} | Status: {b.status}")
        y -= 20
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"attendance_report_event_{event_id}.pdf", mimetype='application/pdf')


@report_bp.route('/vendors/<int:event_id>', methods=['GET'])
@role_required('admin', 'super_admin')
def vendor_report(event_id):
    event = check_event_access(event_id)
    if not event:
        return jsonify({"error": "Access denied"}), 403

    vendors = Vendor.query.filter_by(event_id=event_id).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Vendors"
    ws.append(["Vendor ID", "User ID", "Service Type"])
    for v in vendors:
        ws.append([v.id, v.user_id, v.service_type])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"vendor_report_event_{event_id}.xlsx",
                      mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@report_bp.route('/payments/<int:event_id>', methods=['GET'])
@role_required('admin', 'super_admin')
def payment_report(event_id):
    event = check_event_access(event_id)
    if not event:
        return jsonify({"error": "Access denied"}), 403

    bookings = Booking.query.filter_by(event_id=event_id).all()
    booking_ids = [b.id for b in bookings]
    payments = Payment.query.filter(Payment.booking_id.in_(booking_ids)).all()

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    p.drawString(50, y, f"Payment Report - {event.name}")
    y -= 30
    for pay in payments:
        p.drawString(50, y, f"Booking ID: {pay.booking_id} | Amount: {pay.amount} | Status: {pay.status}")
        y -= 20
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"payment_report_event_{event_id}.pdf", mimetype='application/pdf')