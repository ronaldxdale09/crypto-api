from ninja import Schema
from .models import *

class UserSchema(Schema):
    name: str
    email: str
    password:str