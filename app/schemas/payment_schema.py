from marshmallow import Schema, fields, validate

class PaymentSchema(Schema):
  booking_id = fields.Int(required=True)
  amount = fields.Float(required=True)

class PaymentUpdateSchema(Schema):
  status = fields.Str(required=True, validate=validate.OneOf(['pending', 'paid', 'refunded']))
