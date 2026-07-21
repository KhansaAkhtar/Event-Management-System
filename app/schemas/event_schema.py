from marshmallow import Schema, fields

class EventSchema(Schema):
    name = fields.Str(required=True)
    date = fields.Str(required=True)
    venue = fields.Str(required=True)
    capacity = fields.Int(required=True)
    price = fields.Float(required=True)
    description = fields.Str()
    status = fields.Str()

class EventRequestSchema(Schema):
    name = fields.Str(required=True)
    date = fields.Str(required=True)
    venue = fields.Str(required=True)
    capacity = fields.Int(required=True)
    description = fields.Str()


class EventApprovalSchema(Schema):
    price = fields.Float(required=True)