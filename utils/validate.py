from json import dumps, loads

def validate(request_data, schema):
    data = schema.load(request_data)
    return loads(dumps(data, default=str))