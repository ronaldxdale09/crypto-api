from ninja import Router
from .models import *
from .forms import *
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
import random
import string
import secrets
from wallet.models import *
from django.contrib.auth.hashers import check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from wallet.models import *
from crypto_currency.models import *

router = Router()

#Get Function
@router.get('/getUser', response=list[UserSchema])
def get_user(request):
    users = User.objects.all()
    return [UserSchema(name=user.name, email=user.email, password=user.password) for user in users]

@router.get('user={user_id}', response=UserWalletResponseSchema)
def user(request, user_id: int):
    user = get_object_or_404(User, id=user_id)
    user_detail_instance = UserDetail.objects.filter(user_id=user_id).first()
    wallet_instance = Wallet.objects.filter(user_id=user).first()
    
    wallet_balances = WalletBalance.objects.filter(wallet=wallet_instance) if wallet_instance else []

    balance_data = [
        {
            "wallet_id": balance.wallet.id if balance.wallet else None,
            "crypto_id": balance.cryptocurrency.id if balance.cryptocurrency else None,
            "network_id": balance.network.id if balance.network else None,
            "balance": float(balance.balance)
        }
        for balance in wallet_balances
    ]

    return {
        "user": {"email": user.email},
        "user_detail": {
            "phone_number": user_detail_instance.phone_number if user_detail_instance else None,
            "secret_phrase": user_detail_instance.secret_phrase if user_detail_instance else None,
            "is_verified": user_detail_instance.is_verified if user_detail_instance else None,
            "tier": user_detail_instance.tier if user_detail_instance else None,
            "trading_fee_rate": user_detail_instance.trading_fee_rate if user_detail_instance else None,
            "ip_address": user_detail_instance.ip_address if user_detail_instance else None,
            "last_login_session": user_detail_instance.last_login_session if user_detail_instance else None,
            "previous_ip_address": user_detail_instance.previous_ip_address if user_detail_instance else None,
            "referral_code": user_detail_instance.referral_code if user_detail_instance else None,
            "status": user_detail_instance.status if user_detail_instance else None,
        } if user_detail_instance else None,
        "wallet": {
            "wallet_id": wallet_instance.id if wallet_instance else None,
            "balances": balance_data
        } if wallet_instance else None,
    }





#Login Function
@router.post('/login')
def user_login(request, form: LoginUserSchema):
    try:
        validate_email(form.email)
    except ValidationError:
        return {"error": "Invalid email format"}
    
    user_instance = get_object_or_404(User, email=form.email)
    user_id = user_instance.id

    if not check_password(form.password, user_instance.password):
        return {"error": "Invalid email or password!"}
    
    wallet_instance = Wallet.objects.get(user_id=user_id)
    if not wallet_instance:
        return {"error": "Wallet not found for this user"}
    
    return {
        "success": True,
        "user_id":user_id,
        "wallet_id":wallet_instance.id,
        "email":user_instance.email
    }

#CREATE
#user registration functionality
@router.post('/signup')
def signup_user(request, form:SingupUserSchema):
    try:
        validate_email(form.email)
    except ValidationError:
        return {"error": "Invalid email format"}
    
    if User.objects.filter(email=form.email).exists():
        return {"error": "Email already use"}

    if form.password != form.confirm_password:
        return {"error": "Password do not match!"}
    
    user = User.objects.create(
        email=form.email,
        password=make_password(form.password),
    )
    print("Received data:", form.email, form.password, form.confirm_password)
    #Creating wallet instance
    wallet = Wallet.objects.create()
    wallet.user_id.add(user)

    # Initialize WalletBalance for each cryptocurrency
    cryptocurrencies = Cryptocurrency.objects.all()
    WalletBalance.objects.bulk_create([
        WalletBalance(wallet=wallet, cryptocurrency=crypto, balance=0.0)
        for crypto in cryptocurrencies
    ])
   
    return {
    
        "success": "The account was successfully signed up!",
        "user_id": user.id,
        "wallet_id": wallet.id,
        "cryptocurrencies": [crypto.symbol for crypto in cryptocurrencies]
    }

#To generate a code for referral
def RandomReferralCodeGenerator(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

#To generate a secret phrase
def SecretPhraseGenerator(length=12):
    code = string.ascii_letters + string.digits
    return ''.join(secrets.choice(code) for _ in range(length))

#To create user details/addtional signup info needed
@router.post('/user_details/{userId}')
def user_details(request, userId: int, form: CreateUserDetailSchema):
    user_instance = get_object_or_404(User, id=userId)
    referral_code = form.referral_code or RandomReferralCodeGenerator()
    secret_phrase = form.secret_phrase or SecretPhraseGenerator()
    user_detail=UserDetail.objects.create(
        user_id = user_instance,
        phone_number=form.phone_number,
        secret_phrase=secret_phrase,
        tier=form.tier,
        trading_fee_rate = form.trading_fee_rate,
        ip_address = form.ip_address,
        referral_code = referral_code,
    )
    user_detail.save()
    return{
        "success": True,
        "user_detail_id": user_detail.id,
        "referral_code": user_detail.referral_code,
        "secret_phrase": user_detail.secret_phrase
    }



#UPDATE
#user edit profile after the signup using email and setting up the password
@router.put('/edit_profile/{userId}')
def edit_profile(request, userId: int, form: UpdateUserSchema):
    user_instance = get_object_or_404(User, id=userId)
    user_instance.name = form.name
    user_instance.save()
    
    return {"success": True, "updated_name": user_instance.name}