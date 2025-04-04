from ninja import Router, UploadedFile, File, Form  
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
import jwt
import uuid
from django.conf import settings
import requests 
from ninja.security import HttpBearer
import datetime
from functools import lru_cache
import ipaddress
import socket


router = Router()

API_KEY = "A20RqFwVktRxxRqrKBtmi6ud"
WALLET_API_URL = "https://wallet-app-api-main-m41zlt.laravel.cloud/api/v1/user-wallets"



def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            JWT_SIGNING_KEY = getattr(settings, "JWT_SIGNING_KEY", None)
            payload = jwt.decode(token, JWT_SIGNING_KEY, algorithms=["HS256"])
            email: str = payload.get("email")

            if email is None:
                return None
        except jwt.PyJWTError as e:
            return None
        
        return email
    

# Define Schema for request validation and documentation
class KYCUploadSchema(Schema):
    document_type: str
    
# def create_jwt_token(user):
#     JWT_SIGNING_KEY = getattr(settings, "JWT_SIGNING_KEY", None)
#     payload = {"email": user.email}
#     token = jwt.encode(payload, JWT_SIGNING_KEY, algorithm="HS256")
#     return token

def generate_uid(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

#To generate a code for referral
def RandomReferralCodeGenerator(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

#To generate a secret phrase
def SecretPhraseGenerator(length=12):
    code = string.ascii_letters + string.digits
    return ''.join(secrets.choice(code) for _ in range(length))

#Get Function
@router.get('/getUser', response=list[UserSchema])
def get_user(request):
    users = User.objects.all()
    return [UserSchema(name=user.name, email=user.email, password=user.password) for user in users]

@router.get('getUserInformation/', tags=["User Account"])
def user_information(request, user_id: int):
    user = get_object_or_404(User, id=user_id)
    user_detail = UserDetail.objects.filter(user_id=user_id).first()

    # Format the data for JSON response
    data = {
        "user": {
            "name": user.name,
            "email": user.email,
            "uid": user.uid,
            "secret_phrase": user.secret_phrase,
            "referral_code": user.referral_code,
            "role": user.role_id.first().role if user.role_id.exists() else None
        },
        "user_detail": {
            "user_profile": user_detail.user_profile if user_detail else None,
            "phone_number": user_detail.phone_number if user_detail else None,
            "is_verified": user_detail.is_verified if user_detail else None,
            "tier": user_detail.tier if user_detail else None,
            "trading_fee": user_detail.trading_fee_rate if user_detail else None,
            "ip_address": user_detail.ip_address if user_detail else None,
            "last_login_session": user_detail.last_login_session if user_detail else None,
            "previous_ip_address": user_detail.previous_ip_address if user_detail else None,
            "status": user_detail.status if user_detail else None
        },
    }

    return JsonResponse(data)

def get_user_ip(request):
    """
    Get the most reliable user IP address in a single function.
    Prioritizes public IP from external services over request headers.
    
    Args:
        request: The HTTP request object
        
    Returns:
        str: The user's public IP address or "Unknown"
    """
    # Step 1: Try to get client IP from request headers
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    client_ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
    
    # Step 2: Check if client IP is private or if we should get public IP anyway
    is_private = True
    if client_ip:
        try:
            is_private = ipaddress.ip_address(client_ip).is_private
        except ValueError:
            pass
    
    # Step 3: If client IP is private or we want to ensure we get public IP
    if is_private:
        # Use cached function for better performance
        public_ip = _get_public_ip()
        if public_ip:
            return public_ip
    
    # Step 4: Return non-private client IP if available
    if client_ip and not is_private:
        return client_ip
    
    # Step 5: Final fallback
    return "Unknown"

@lru_cache(maxsize=128)
def _get_public_ip():
    """
    Internal cached function to get public IP from external services.
    """
    services = [
        'https://api.ipify.org',
        'https://ifconfig.me/ip',
        'https://ipinfo.io/ip',
        'https://icanhazip.com'
    ]
    
    for service in services:
        try:
            response = requests.get(service, timeout=3)
            if response.status_code == 200:
                ip = response.text.strip()
                if ip:
                    try:
                        # Validate it's not a private IP
                        if not ipaddress.ip_address(ip).is_private:
                            return ip
                    except ValueError:
                        continue
        except Exception:
            continue
    
    return None

@router.post('/login')
def user_login(request, form: LoginUserSchema):
    """
    User login endpoint.
    
    Validates email and password, updates IP information,
    and returns user credentials and IP address.
    
    Args:
        request: The HTTP request object
        form: Login form with email and password
        
    Returns:
        dict: Login response with user information and IP address
    """
    # Step 1: Validate email format
    try:
        validate_email(form.email)
    except ValidationError:
        return {
            "success": False,
            "error": "Invalid email format"
        }
    
    # Step 2: Get and verify user
    try:
        user = get_object_or_404(User, email=form.email)
    except:
        return {
            "success": False,
            "error": "User not found"
        }
    
    # Step 3: Verify password
    if not check_password(form.password, user.password):
        return {
            "success": False, 
            "error": "Invalid email or password"
        }
    
    # Step 4: Get user's IP address with optimized function
    user_ip = get_user_ip(request)
    
    # Step 5: Update user IP information
    try:
        user_detail, created = UserDetail.objects.get_or_create(
            user=user,
            defaults={'ip_address': user_ip}
        )
        
        # Store previous IP if different from current
        if user_detail.ip_address and user_detail.ip_address != user_ip:
            user_detail.previous_ip_address = user_detail.ip_address
        
        # Update current IP and login session time
        user_detail.ip_address = user_ip
        user_detail.last_login_session = timezone.now()
        user_detail.save()
    except Exception as e:
        # If updating user detail fails, continue anyway (non-critical)
        pass
    
    # # Step 6: Try to get wallet information
    # try:
    #     from wallet.models import Wallet
    #     wallet = Wallet.objects.get(user_id=user.id)
    #     wallet_id = wallet.id
    # except Exception:
    #     wallet_id = None

    # Step 6: Fetch JWT token from database
    jwt_token = user.jwt_token
    if not jwt_token:
        return {
            "success": False,
            "error": "JWT token not found"
        }
    
    # Step 7: Return success response with user info
    return {
        "success": True,
        "user_id": user.id,
        "email": user.email,
        "uid": user.uid,
        "jwt_token": jwt_token,
        # "wallet_id": wallet_id,
        "ip_address": user_ip
    }
#CREATE
#user registration functionality
@router.post('/signup',
             tags=["User Account"],)
def signup_user(request, form:SingupUserSchema):
    try:
        validate_email(form.email)
    except ValidationError:
        return {"error": "Invalid email format"}
    
    if User.objects.filter(email=form.email).exists():
        return {"error": "Email already use"}

    if form.password != form.confirm_password:
        return {"error": "Password do not match!"}
    
    referral_code = RandomReferralCodeGenerator()
    secret_phrase = SecretPhraseGenerator()
    uid = generate_uid()
   
    user = User.objects.create(
        email=form.email,
        password=make_password(form.password),
        referral_code = referral_code,
        secret_phrase = secret_phrase,
        uid = uid
    )
    print("Received data:", form.email, form.password, form.confirm_password)

    # Assign 'Client' role to the user
    client_role = Role.objects.get(role='client')
    user.role_id.add(client_role)

    # Create wallet linked to user
    wallet = Wallet.objects.create(
        available_balance=0,
        wallet_address=None,
        is_active=True
    )
    wallet.user_id.add(user)

    # Initialize UserAsset for each cryptocurrency
    cryptocurrencies = Cryptocurrency.objects.all()
    UserAsset.objects.bulk_create([
        UserAsset(wallet=wallet, cryptocurrency=crypto, balance=0.0)
        for crypto in cryptocurrencies
    ])

    # Generate JWT token
    payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }

    JWT_SIGNING_KEY = getattr(settings, "JWT_SIGNING_KEY", None)
    encoded_token = jwt.encode(payload, JWT_SIGNING_KEY, algorithm="HS256")
    user.jwt_token = encoded_token
    user.save()
    
    # Send UID to wallet API   
    API_KEY = "A20RqFwVktRxxRqrKBtmi6ud"
    WALLET_API_URL = "https://wallet-app-api-main-m41zlt.laravel.cloud/api/v1/user-details"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # You can either send as query parameter
    api_response = requests.post(
        f"{WALLET_API_URL}?apikey={API_KEY}",
        json={"uid": uid},
        headers=headers
    )

    
    # Check if API call was successful
    if api_response.status_code != 200:
        # If API call failed, you may want to delete the created user
        # or handle the error differently
        User.objects.filter(id=user.id).delete()
        return {"error": f"Failed to register with wallet service: {api_response.text}"}
        
    return {
        "success": "The account was successfully signed up!",
        "user_id": user.id,
        'jwt_token': encoded_token,
        "role": "Client",
        "referral_code": referral_code,
        "secret_phrase": secret_phrase,
        "uid": uid,
        "cryptocurrencies": [crypto.symbol for crypto in cryptocurrencies],
    }


#To create user details/addtional signup info needed
# @router.post('/user_details/{userId}')
# def user_details(request, userId: int, form: CreateUserDetailSchema):
#     user_instance = get_object_or_404(User, id=userId)

#     user_detail=UserDetail.objects.create(
#         user_id = user_instance,
#         phone_number=form.phone_number,
#         tier=form.tier,
#         trading_fee_rate = form.trading_fee_rate,
#         ip_address = form.ip_address,
#     )
#     user_detail.save()
#     return{
#         "success": True,
#         "user_detail_id": user_detail.id,
#         "referral_code": user_detail.referral_code,
#         "secret_phrase": user_detail.secret_phrase,
#     }

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
            
            # Use the "image" bucket and a "profiles" folder
            bucket_name = "image"
            folder_name = "profiles"
            supabase_url = settings.SUPABASE_URL
            storage_url = f"{supabase_url}/storage/v1/object/{bucket_name}/{folder_name}/{filename}"
            
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
                public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{folder_name}/{filename}"
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

@router.post('/upload-kyc/user={user_id}', 
             tags=["User Account"],
             summary="Upload KYC documents")
def upload_kyc(request, user_id: int):
    """
    Upload KYC (Know Your Customer) verification documents
    
    This endpoint allows users to submit their identification documents for verification.
    """
    from django.conf import settings
    
    # Check if user exists
    user = get_object_or_404(User, id=user_id)
    
    # Prevent duplicate KYC records
    if KnowYourCustomer.objects.filter(user_id=user).exists():
        return {
            "success": False,
            "message": "KYC record already exists for this user"
        }
    
    # Extract data from request
    document_type = request.POST.get('document_type')
    captured_selfie = request.FILES.get('captured_selfie')
    front_captured_image = request.FILES.get('front_captured_image')
    back_captured_image = request.FILES.get('back_captured_image')
    
    # Ensure document type is valid
    valid_document_types = [doc[0] for doc in KnowYourCustomer.DOCUMENT_TYPES]
    if not document_type or document_type not in valid_document_types:
        return {
            "success": False,
            "message": f"Invalid document type: {document_type}. Valid types are: {', '.join(valid_document_types)}"
        }
    
    # Check if all required files are provided
    if not all([captured_selfie, front_captured_image, back_captured_image]):
        return {
            "success": False,
            "message": "All required files (selfie, front and back of ID) must be uploaded"
        }
    
    # Upload selfie to Supabase
    try:
        # Read file data
        selfie_content = captured_selfie.read()
        selfie_size = len(selfie_content)
        selfie_type = captured_selfie.content_type
        
        # Generate a unique filename
        selfie_filename = f"selfie_{user_id}_{uuid.uuid4().hex[:8]}.{captured_selfie.name.split('.')[-1]}"
        
        # Changed bucket name from crypto_app to image
        bucket_name = "image"
        folder_name = "kyc"
        supabase_url = settings.SUPABASE_URL
        selfie_storage_url = f"{supabase_url}/storage/v1/object/{bucket_name}/{folder_name}/{selfie_filename}"
        
        # Set up headers
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            "Content-Type": selfie_type,
        }
        
        # Upload the selfie
        selfie_response = requests.post(
            selfie_storage_url,
            headers=headers,
            data=selfie_content
        )
        
        if selfie_response.status_code not in [200, 201]:
            return {
                "success": False,
                "message": f"Failed to upload selfie: {selfie_response.status_code} - {selfie_response.text}"
            }
            
        selfie_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{folder_name}/{selfie_filename}"
        
        # Upload front ID image
        front_content = front_captured_image.read()
        front_type = front_captured_image.content_type
        front_filename = f"front_id_{user_id}_{uuid.uuid4().hex[:8]}.{front_captured_image.name.split('.')[-1]}"
        front_storage_url = f"{supabase_url}/storage/v1/object/{bucket_name}/{folder_name}/{front_filename}"
        
        front_response = requests.post(
            front_storage_url,
            headers={
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                "Content-Type": front_type,
            },
            data=front_content
        )
        
        if front_response.status_code not in [200, 201]:
            return {
                "success": False,
                "message": f"Failed to upload front ID: {front_response.status_code} - {front_response.text}"
            }
            
        front_id_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{folder_name}/{front_filename}"
        
        # Upload back ID image
        back_content = back_captured_image.read()
        back_type = back_captured_image.content_type
        back_filename = f"back_id_{user_id}_{uuid.uuid4().hex[:8]}.{back_captured_image.name.split('.')[-1]}"
        back_storage_url = f"{supabase_url}/storage/v1/object/{bucket_name}/{folder_name}/{back_filename}"
        
        back_response = requests.post(
            back_storage_url,
            headers={
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                "Content-Type": back_type,
            },
            data=back_content
        )
        
        if back_response.status_code not in [200, 201]:
            return {
                "success": False,
                "message": f"Failed to upload back ID: {back_response.status_code} - {back_response.text}"
            }
            
        back_id_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{folder_name}/{back_filename}"
        
    except Exception as e:
        import traceback
        print(f"Error uploading KYC files: {str(e)}")
        print(traceback.format_exc())
        return {
            "success": False,
            "message": f"Error uploading KYC files: {str(e)}"
        }
    
    # Create KYC record
    try:
        kyc = KnowYourCustomer.objects.create(
            user_id=user,
            document_type=document_type,
            captured_selfie=selfie_url,
            front_captured_image=front_id_url,
            back_captured_image=back_id_url,
        )
    except Exception as e:
        import traceback
        print(f"Error creating KYC record: {str(e)}")
        print(traceback.format_exc())
        return {
            "success": False,
            "message": f"Error creating KYC record: {str(e)}"
        }
    
    user_detail_instance = UserDetail.objects.get(user_id=user_id)
    user_detail_instance.is_verified = True
    user_detail_instance.save()
    
    return {
        "success": True,
        "message": "KYC documents uploaded successfully",
        "user_id": user.id,
        "document_type": kyc.document_type,
        "selfie_url": selfie_url,
        "front_id_url": front_id_url,
        "back_id_url": back_id_url,
        "is_verified": user_detail_instance.is_verified,
    }