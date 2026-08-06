from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.schemas.user_schema import UserRegisterSchema, UserLoginSchema
from app.utils.email_utils import send_email
from app.utils.audit_utils import log_action
from app import limiter
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """
    Register a New User
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - contact
            - password
            - role
          properties:
            name:
              type: string
              example: Ali Khan
            email:
              type: string
              example: ali@example.com
            contact:
              type: string
              example: "03001234567"
            password:
              type: string
              example: mypassword123
            role:
              type: string
              enum: [user, vendor]
              example: user
    responses:
      201:
        description: User registered successfully
      400:
        description: Validation error (invalid email, weak password, etc.)
      409:
        description: Email already registered
      429:
        description: Rate limit exceeded
    """
    try:
        data = UserRegisterSchema().load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 409

    hashed_pw = generate_password_hash(data['password'])

    new_user = User(
        name=data['name'],
        email=data['email'],
        contact=data.get('contact'),
        password_hash=hashed_pw,
        role=data['role']
    )

    db.session.add(new_user)
    db.session.commit()

    send_email(
        subject="Welcome to Event Hub!",
        recipients=[new_user.email],
        body=f"Hi {new_user.name},\n\nYour account has been created successfully with the role '{new_user.role}'.\n\nWelcome aboard!"
    )

    return jsonify({"message": "User registered successfully"}), 201


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """
    User Login
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: mypassword123
    responses:
      200:
        description: Login successful, returns JWT token
        examples:
          application/json: {"message": "Login successful", "access_token": "eyJ...", "role": "user", "name": "Ali", "id": 1}
      401:
        description: Invalid email or password
      403:
        description: Account locked due to failed attempts
      429:
        description: Too many login attempts, rate limit exceeded
    """
    try:
        data = UserLoginSchema().load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
        return jsonify({"error": f"Account locked. Try again in {remaining} minute(s)."}), 403

    if not check_password_hash(user.password_hash, data['password']):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            user.failed_login_attempts = 0
            db.session.commit()
            return jsonify({"error": "Account locked due to too many failed attempts. Try again in 15 minutes."}), 403

        db.session.commit()
        return jsonify({"error": "Invalid email or password"}), 401

    user.failed_login_attempts = 0
    user.locked_until = None
    db.session.commit()

    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

    log_action(user.id, "login", f"User {user.email} logged in")

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "role": user.role,
        "name": user.name,
        "id": user.id
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    log_action(current_user_id, "logout", f"User {user.email if user else current_user_id} logged out")
    return jsonify({"message": "Logged out successfully"}), 200