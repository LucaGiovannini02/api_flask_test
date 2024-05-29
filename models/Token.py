from marshmallow import Schema, fields

class Token(Schema):
    Token = fields.String(required=True)