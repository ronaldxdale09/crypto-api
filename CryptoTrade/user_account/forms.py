from ninja import Schema, UploadedFile
from .models import *
from pydantic import BaseModel
from typing import Optional, List
from wallet.forms import *

class UserSchema(Schema):
    # name: Opstr
    email: str
    # password:str

class UserDetailSchema(Schema):
    phone_number: Optional[str]
    secret_phrase: Optional[str]
    is_verified: Optional[bool] 
    tier: Optional[int] 
    trading_fee_rate: Optional[float]
    ip_address: Optional[str] 
    last_login_session: Optional[str] 
    previous_ip_address: Optional[str] 
    referral_code: Optional[str]
    status: Optional[str]
    # role: "Client"

# class UserWalletResponseSchema(Schema):
#     user: UserSchema
#     user_detail: Optional[UserDetailSchema] = None
#     wallet: Optional[WalletSchema] = None
#     wallet_balances: List[UserAssetSchema] = []


# class UserWalletResponseSchema(Schema):
#     user: UserSchema
#     user_detail: UserDetailSchema
#     wallet: WalletSchema

class SingupUserSchema(Schema):
    email: str
    password:str
    confirm_password:str
    
class LoginUserSchema(BaseModel):
    email: str
    password:str

class UpdateUserSchema(Schema):
    name:str
    # email:str
    phone_number: str 
    user_profile: Optional[str]
    # is_verified: bool
    # tier: bool 
    # trading_fee_rate: str 
    # last_login_session: str 
    # previous_ip_address: str 
    # status: str
    # referral_code: str
    # secret_phrase: str 

class CreateUserDetailSchema(Schema):
    phone_number: str 
 
    is_verified: bool
    tier: bool 
    trading_fee_rate: str 
    ip_address: str 
    last_login_session: str 
    previous_ip_address: str 

    status: str
    role:str

class OTPVerificationSchema(Schema):
    email: str
    otp: str

class OTPRequestSchema(Schema):
    email: str

class MessageResponseSchema(Schema):
    message: str

class ResetPasswordSchema(Schema):
    email:str
    otp:str
    new_password:str
    confirm_password:str

class UpdateUserCountry(Schema):
    user_id: int
    country: str


class PasswordResetSchema(Schema):
    email:str
    currentPassword:str

class EmailResetSchema(Schema):
    email:str

class EmailChangeSchema(Schema):
    email:str
    otp:str
    new_email:str
