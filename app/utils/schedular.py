from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app.models.event import Event
from app.models.booking import Booking
from app.models.user import User
from app.models.reminder_log import ReminderLog
from app.utils.email_utils import send_email


def send_event_reminders(app):
    with app.app_context():
        from app import db

        now = datetime.utcnow()
        target_date = (now + timedelta(hours=24)).strftime('%Y-%m-%d')

        # Sirf wo events jo 24 ghante baad hain, aur cancelled nahi hain
        upcoming_events = Event.query.filter(
            Event.date == target_date,
            Event.status != 'cancelled'
        ).all()

        for event in upcoming_events:
            bookings = Booking.query.filter_by(event_id=event.id, status='registered').all()

            for booking in bookings:
                already_sent = ReminderLog.query.filter_by(booking_id=booking.id).first()
                if already_sent:
                    continue

                user = User.query.get(booking.user_id)
                if not user:
                    continue

                send_email(
                    subject=f"Reminder: {event.name} is Tomorrow!",
                    recipients=[user.email],
                    body=f"Hi {user.name},\n\nThis is a reminder that '{event.name}' is happening tomorrow ({event.date}) at {event.venue}.\n\nSee you there!"
                )

                db.session.add(ReminderLog(booking_id=booking.id))
                db.session.commit()


def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: send_event_reminders(app), trigger="interval", hours=1)
    scheduler.start()