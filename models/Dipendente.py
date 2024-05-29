from marshmallow import Schema, fields, validate

class Dipendente(Schema):
    Nome = fields.String(required=True)
    Cognome = fields.String(required=True)
    Nascita = fields.Date(required=True)
    Comune = fields.String(required=True)
    Sesso = fields.String(required=True, validate=validate.OneOf(["M", "F"]))
    Token = fields.String(required=True)