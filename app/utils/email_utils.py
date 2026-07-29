from flask_mail import Message
from app import mail
from threading import Thread
from flask import current_app

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")

def send_email(subject, recipients, body):
    app = current_app._get_current_object()
    msg = Message(subject=subject, recipients=recipients, body=body)
    Thread(target=send_async_email, args=(app, msg)).start()