from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from config import Config
from flasgger import Swagger
from flask_limiter import Limiter
from flask_mail import Mail
from flask_limiter.util import get_remote_address
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Event Management System API",
        "description": "REST API for managing events, bookings, vendors, payments, and reports with role-based access control.",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Enter: Bearer <your_jwt_token>"
        }
    }
}

swagger = Swagger(template=swagger_template)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    swagger.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    from app.models import user, event, booking, vendor, payment, waitlist, booking_log, reminder_log, audit_log
    from app.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from app.routes.user_routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/users')
    from app.routes.event_routes import event_bp
    app.register_blueprint(event_bp, url_prefix='/events')
    from app.routes.booking_routes import booking_bp
    app.register_blueprint(booking_bp, url_prefix='/bookings')
    from app.routes.vendor_routes import vendor_bp
    app.register_blueprint(vendor_bp, url_prefix='/vendors')
    from app.routes.payment_routes import payment_bp
    app.register_blueprint(payment_bp, url_prefix='/payments')
    from app.routes.report_routes import report_bp
    app.register_blueprint(report_bp, url_prefix='/reports')
    from app.routes.view_routes import view_bp
    app.register_blueprint(view_bp)
    from app.utils.schedular import start_scheduler
    start_scheduler(app)
    return app
 
