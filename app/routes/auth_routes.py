from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app import db
from app.models.user import User
from app.schemas.user_schema import UserRegisterSchema, UserLoginSchema

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = UserRegisterSchema().load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    # Check if email already exists (prevents duplicate accounts)
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

    return jsonify({"message": "User registered successfully"}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = UserLoginSchema().load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "role": user.role,
        "name": user.name
    }), 200

