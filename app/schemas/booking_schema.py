from marshmallow import Schema, fields

class BookingSchema(Schema):
  event_id = fields.Int(required=True)