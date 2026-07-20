from marshmallow import Schema, fields

class VendorSchema(Schema):
    service_type = fields.Str(required=True)
    event_id = fields.Int(required=True)