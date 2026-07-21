from marshmallow import Schema, fields, validate

class UserRegisterSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    contact = fields.Str(required=True, validate=validate.Regexp(r'^\d{10,15}$', error="Contact must be 10-15 digits"))
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(required=True, validate=validate.OneOf(['vendor', 'user']))

class UserLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)