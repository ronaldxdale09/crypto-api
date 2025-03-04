from ninja import Router, UploadedFile, File
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
from ninja.files import UploadedFile

import uuid
from django.conf import settings
import requests 



router = Router()

#Get Function
@router.get('/getUser', response=list[UserSchema])
def get_user(request):
    users = User.objects.all()
    return [UserSchema(name=user.name, email=user.email, password=user.password) for user in users]

@router.get('getUserInformation/')
def user_information(request, user_id: int):
    user = get_object_or_404(User, id=user_id)
    user_detail = UserDetail.objects.filter(user_id=user_id).first()
    wallet = Wallet.objects.filter(user_id=user).first()
    wallet_balances = WalletBalance.objects.filter(wallet=wallet).select_related('cryptocurrency') if wallet else []

    # Format the data for JSON response
    data = {
        "user": {
            "name": user.name,
            "email": user.email
        },
        "user_detail": {
            "phone_number": user_detail.phone_number if user_detail else None,
            "is_verified": user_detail.is_verified if user_detail else None,
            "secret_phrase": user_detail.secret_phrase if user_detail else None,
            "tier": user_detail.tier if user_detail else None,
            "trading_fee": user_detail.trading_fee_rate if user_detail else None,
            "ip_address": user_detail.ip_address if user_detail else None,
            "last_login_sesson": user_detail.last_login_session if user_detail else None,
            "previous_ip_address": user_detail.previous_ip_address if user_detail else None,
            "referral_code": user_detail.referral_code if user_detail else None,
            "status": user_detail.status if user_detail else None,
        },
        "wallet": {
            "wallet_address": wallet.wallet_address if wallet else None,
            "available_balance": wallet.available_balance if wallet else None,
        },
        "wallet_balances": [
            {
                "crypto_id": balance.cryptocurrency.id if balance.cryptocurrency else None,
                "crypto_symbol": balance.cryptocurrency.symbol if balance.cryptocurrency else "N/A",
                "network": balance.network.name if balance.network else "Unknown",
                "balance": float(balance.balance) if balance.balance != 0 else 0.0    
            }
            for balance in wallet_balances
        ]
    }

    return JsonResponse(data)




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

@router.post('/edit_profile/user={userId}')
def edit_profile(request, userId: int):
    from django.conf import settings
    
    # Get user instance
    user_instance = get_object_or_404(User, id=userId)
    
    # Extract data from request
    name = request.POST.get('name')
    phone_number = request.POST.get('phone_number')
    user_profile = request.FILES.get('user_profile')
    
    # Update User fields if provided
    if name:
        user_instance.name = name
        user_instance.save()
    
    # Get or create UserDetail
    user_detail, created = UserDetail.objects.get_or_create(user_id=user_instance)
    
    # Update phone number if provided
    if phone_number:
        user_detail.phone_number = phone_number
    
    # Upload profile image to Supabase Storage if provided
    if user_profile:
        try:
            # Read file data
            file_content = user_profile.read()
            file_size = len(file_content)
            file_type = user_profile.content_type
            
            # Print debug info
            print(f"Uploading file: {user_profile.name}, Size: {file_size}, Type: {file_type}")
            
            # Generate a unique filename (without folder path)
            filename = f"user_profile_{userId}_{uuid.uuid4().hex[:8]}.{user_profile.name.split('.')[-1]}"
            
            bucket_name = "crypto_app"
            supabase_url = settings.SUPABASE_URL
            storage_url = f"{supabase_url}/storage/v1/object/{bucket_name}/{filename}"
            
            print(f"Upload URL: {storage_url}")
            
            # Set up headers with Supabase API key
            headers = {
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",  # Use service_role key
                "Content-Type": file_type,
            }
            
            # Upload the file to Supabase Storage
            upload_response = requests.post(
                storage_url,
                headers=headers,
                data=file_content
            )
            
            # Debug response
            print(f"Upload status code: {upload_response.status_code}")
            print(f"Upload response: {upload_response.text[:200]}...")  # Print first 200 chars
            
            if upload_response.status_code in [200, 201]:
                # Calculate the public URL
                public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{filename}"
                user_detail.user_profile = public_url
                print(f"File uploaded successfully: {public_url}")
            else:
                print(f"Error uploading to Supabase: {upload_response.text}")
                return {
                    "success": False,
                    "message": f"Failed to upload image: {upload_response.status_code} - {upload_response.text}"
                }
                
        except Exception as e:
            import traceback
            print(f"Error uploading image: {str(e)}")
            print(traceback.format_exc())
            return {
                "success": False,
                "message": f"Error uploading image: {str(e)}"
            }
    
    user_detail.save()
    
    # Customize response message
    creation_message = "User details created" if created else "User details updated"
    
    return {
        "success": True,
        "message": creation_message,
        "user": {
            "id": user_instance.id,
            "name": user_instance.name,
            "email": user_instance.email
        },
        "user_detail": {
            "phone_number": user_detail.phone_number,
            "is_verified": user_detail.is_verified,
            "tier": user_detail.tier,
            "trading_fee_rate": user_detail.trading_fee_rate,
            "last_login_session": user_detail.last_login_session,
            "previous_ip_address": user_detail.previous_ip_address,
            "status": user_detail.status,
            "user_profile": user_detail.user_profile
        }
    }