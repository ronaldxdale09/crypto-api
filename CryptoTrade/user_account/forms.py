from ninja import Schema
from .models import *
from pydantic import BaseModel

class UserSchema(Schema):
    # name: Opstr
    email: str
    password:str

class SingupUserSchema(Schema):
    email: str
    password:str
    confirm_password:str

class LoginUserSchema(BaseModel):
    email: str
    password:str

class UpdateUserSchema(Schema):
    name:str

class CreateUserDetailSchema(Schema):
    phone_number: str 
    secret_phrase: str 
    is_verified: bool
    tier: bool 
    trading_fee_rate: str 
    ip_address: str 
    last_login_session: str 
    previous_ip_address: str 
    referral_code: str
    status: str