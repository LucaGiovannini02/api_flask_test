from marshmallow import Schema, fields

class Login(Schema):
    Email = fields.String(required=True)
    Password = fields.String(required=True)