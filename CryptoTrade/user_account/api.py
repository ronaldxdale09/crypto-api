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
from django.core.mail import send_mail
import pyotp
# from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ObjectDoesNotExist
router = Router()

API_KEY = "A20RqFwVktRxxRqrKBtmi6ud"
WALLET_API_URL = "https://apiv2.bhtokens.com/api/v1/user-wallets"



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
            "jwt_token": user.jwt_token,
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
            "status": user_detail.status if user_detail else None,
            "user_country": user_detail.user_country if user_detail else None,
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
@router.post('/signup', tags=["User Account"])
def signup_user(request, form: SingupUserSchema):
    try:
        validate_email(form.email)
    except ValidationError:
        return {"error": "Invalid email format"}
    
    if User.objects.filter(email=form.email).exists():
        return {"error": "Email already in use"}

    if form.password != form.confirm_password:
        return {"error": "Passwords do not match!"}
    
    referral_code = RandomReferralCodeGenerator()
    secret_phrase = SecretPhraseGenerator()
    uid = generate_uid()
   
    user = User.objects.create(
        email=form.email,
        password=make_password(form.password),
        referral_code=referral_code,
        secret_phrase=secret_phrase,
        uid=uid,
        is_active=False  # Set user as inactive until email is verified
    )
    print("Received data:", form.email, form.password, form.confirm_password)

    # Assign 'Client' role to the user
    client_role = Role.objects.get(role='client')
    user.role_id.add(client_role)

    # Create wallet linked to user
    wallet = Wallet.objects.create(
        available_balance=0,
        wallet_address=None,
        is_active=False  # Keep wallet inactive until email verification
    )
    wallet.user_id.add(user)

    # Initialize UserAsset for each cryptocurrency
    cryptocurrencies = Cryptocurrency.objects.all()
    UserAsset.objects.bulk_create([
        UserAsset(wallet=wallet, cryptocurrency=crypto, balance=0.0)
        for crypto in cryptocurrencies
    ])

    # Generate OTP
    otp = generate_otp(user)
    
    # Send OTP via email
    send_otp_email(form.email, otp)
    
    return {
        "message": "Account created successfully. Please check your email for OTP verification.",
        "user_id": user.id,
        "email": user.email,
        # Don't send JWT token until email is verified
    }
# @router.post('/signup',
#              tags=["User Account"],)
# def signup_user(request, form:SingupUserSchema):
#     try:
#         validate_email(form.email)
#     except ValidationError:
#         return {"error": "Invalid email format"}
    
#     if User.objects.filter(email=form.email).exists():
#         return {"error": "Email already use"}

#     if form.password != form.confirm_password:
#         return {"error": "Password do not match!"}
    
#     referral_code = RandomReferralCodeGenerator()
#     secret_phrase = SecretPhraseGenerator()
#     uid = generate_uid()
   
#     user = User.objects.create(
#         email=form.email,
#         password=make_password(form.password),
#         referral_code = referral_code,
#         secret_phrase = secret_phrase,
#         uid = uid
#     )
#     print("Received data:", form.email, form.password, form.confirm_password)

#     # Assign 'Client' role to the user
#     client_role = Role.objects.get(role='client')
#     user.role_id.add(client_role)

#     # Create wallet linked to user
#     wallet = Wallet.objects.create(
#         available_balance=0,
#         wallet_address=None,
#         is_active=True
#     )
#     wallet.user_id.add(user)

#     # Initialize UserAsset for each cryptocurrency
#     cryptocurrencies = Cryptocurrency.objects.all()
#     UserAsset.objects.bulk_create([
#         UserAsset(wallet=wallet, cryptocurrency=crypto, balance=0.0)
#         for crypto in cryptocurrencies
#     ])

#     # Generate JWT token
#     payload = {
#         "user_id": user.id,
#         "email": user.email,
#         "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
#     }

#     JWT_SIGNING_KEY = getattr(settings, "JWT_SIGNING_KEY", None)
#     encoded_token = jwt.encode(payload, JWT_SIGNING_KEY, algorithm="HS256")
#     user.jwt_token = encoded_token
#     user.save()
    
#     # Send UID to wallet API   
#     API_KEY = "A20RqFwVktRxxRqrKBtmi6ud"
#     WALLET_API_URL = "https://apiv2.bhtokens.com/api/v1/user-details"
    
#     headers = {
#         "Content-Type": "application/json",
#         "Accept": "application/json"
#     }
    
#     # You can either send as query parameter
#     api_response = requests.post(
#         f"{WALLET_API_URL}?apikey={API_KEY}",
#         json={"uid": uid},
#         headers=headers
#     )

    
#     # Check if API call was successful
#     if api_response.status_code != 200:
#         # If API call failed, you may want to delete the created user
#         # or handle the error differently
#         User.objects.filter(id=user.id).delete()
#         return {"error": f"Failed to register with wallet service: {api_response.text}"}
        
#     return {
#         "success": "The account was successfully signed up!",
#         "user_id": user.id,
#         'jwt_token': encoded_token,
#         "role": "Client",
#         "referral_code": referral_code,
#         "secret_phrase": secret_phrase,
#         "uid": uid,
#         "cryptocurrencies": [crypto.symbol for crypto in cryptocurrencies],
#     }


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

    # Send UID to wallet API   
    API_KEY = "A20RqFwVktRxxRqrKBtmi6ud"
    WALLET_API_URL = "https://apiv2.bhtokens.com/api/v1/user-details"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # You can either send as query parameter
    api_response = requests.post(
        f"{WALLET_API_URL}?apikey={API_KEY}",
        json={
            "name": user_instance.name,
            "phone_number":user_detail.phone_number,
            "user_country":user_detail.user_country,
            "ip_address":user_detail.ip_address or ""
            },
        headers=headers
    )

    # Check if API call was successful
    if api_response.status_code != 200:
        # If API call failed, handle the error but don't delete the user
        # as they've already verified their email
        return {"error": f"Failed to register with wallet service: {api_response.text}"}
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

# class KYCUploadSchema(BaseModel):
#     document_type: str

# @router.post('/upload-kyc/user={user_id}', 
#              tags=["User Account"],
#              summary="Upload KYC documents")
# def upload_kyc(
#     request, 
#     user_id: int,
#     document_type: str = Form(..., description="Type of document being uploaded"),
#     captured_selfie: UploadedFile = File(..., description="User's selfie for verification"),
#     front_captured_image: UploadedFile = File(..., description="Front side of the ID document"),
#     back_captured_image: UploadedFile = File(..., description="Back side of the ID document")
# ):
#     """
#     Upload KYC (Know Your Customer) verification documents
    
#     This endpoint allows users to submit their identification documents for verification.
#     """
#     from django.conf import settings
    
#     # Check if user exists
#     user = get_object_or_404(User, id=user_id)
    
#     # Prevent duplicate KYC records
#     if KnowYourCustomer.objects.filter(user_id=user).exists():
#         return {
#             "success": False,
#             "message": "KYC record already exists for this user"
#         }
    
#     # Ensure document type is valid
#     valid_document_types = [doc[0] for doc in KnowYourCustomer.DOCUMENT_TYPES]
#     if not document_type or document_type not in valid_document_types:
#         return {
#             "success": False,
#             "message": f"Invalid document type: {document_type}. Valid types are: {', '.join(valid_document_types)}"
#         }
    
#     # Upload selfie to Supabase
#     try:
#         # Read file data
#         selfie_content = captured_selfie.read()
#         selfie_type = captured_selfie.content_type
        
#         # Generate a unique filename
#         selfie_filename = f"selfie_{user_id}_{uuid.uuid4().hex[:8]}.{captured_selfie.name.split('.')[-1]}"
        
#         bucket_name = "crypto_app"
#         folder_name = "kyc"
#         supabase_url = settings.SUPABASE_URL
#         selfie_storage_url = f"{supabase_url}/storage/v1/object/{bucket_name}/{folder_name}/{selfie_filename}"
        
#         # Set up headers
#         headers = {
#             "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
#             "Content-Type": selfie_type,
#         }
        
#         # Upload the selfie
#         selfie_response = requests.post(
#             selfie_storage_url,
#             headers=headers,
#             data=selfie_content
#         )
        
#         if selfie_response.status_code not in [200, 201]:
#             return {
#                 "success": False,
#                 "message": f"Failed to upload selfie: {selfie_response.status_code} - {selfie_response.text}"
#             }
            
#         selfie_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{folder_name}/{selfie_filename}"
        
#         # Upload front ID image
#         front_content = front_captured_image.read()
#         front_type = front_captured_image.content_type
#         front_filename = f"front_id_{user_id}_{uuid.uuid4().hex[:8]}.{front_captured_image.name.split('.')[-1]}"
#         front_storage_url = f"{supabase_url}/storage/v1/object/{bucket_name}/{folder_name}/{front_filename}"
        
#         front_response = requests.post(
#             front_storage_url,
#             headers={
#                 "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
#                 "Content-Type": front_type,
#             },
#             data=front_content
#         )
        
#         if front_response.status_code not in [200, 201]:
#             return {
#                 "success": False,
#                 "message": f"Failed to upload front ID: {front_response.status_code} - {front_response.text}"
#             }
            
#         front_id_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{folder_name}/{front_filename}"
        
#         # Upload back ID image
#         back_content = back_captured_image.read()
#         back_type = back_captured_image.content_type
#         back_filename = f"back_id_{user_id}_{uuid.uuid4().hex[:8]}.{back_captured_image.name.split('.')[-1]}"
#         back_storage_url = f"{supabase_url}/storage/v1/object/{bucket_name}/{folder_name}/{back_filename}"
        
#         back_response = requests.post(
#             back_storage_url,
#             headers={
#                 "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
#                 "Content-Type": back_type,
#             },
#             data=back_content
#         )
        
#         if back_response.status_code not in [200, 201]:
#             return {
#                 "success": False,
#                 "message": f"Failed to upload back ID: {back_response.status_code} - {back_response.text}"
#             }
            
#         back_id_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{folder_name}/{back_filename}"
        
#     except Exception as e:
#         import traceback
#         print(f"Error uploading KYC files: {str(e)}")
#         print(traceback.format_exc())
#         return {
#             "success": False,
#             "message": f"Error uploading KYC files: {str(e)}"
#         }
    
#     # Create KYC record
#     try:
#         kyc = KnowYourCustomer.objects.create(
#             user_id=user,
#             document_type=document_type,
#             captured_selfie=selfie_url,
#             front_captured_image=front_id_url,
#             back_captured_image=back_id_url,
#         )
#     except Exception as e:
#         import traceback
#         print(f"Error creating KYC record: {str(e)}")
#         print(traceback.format_exc())
#         return {
#             "success": False,
#             "message": f"Error creating KYC record: {str(e)}"
#         }
    
#     user_detail_instance = UserDetail.objects.get(user_id=user_id)
#     user_detail_instance.is_verified = True
#     user_detail_instance.save()
    
#     return {
#         "success": True,
#         "message": "KYC documents uploaded successfully",
#         "user_id": user.id,
#         "document_type": kyc.document_type,
#         "selfie_url": selfie_url,
#         "front_id_url": front_id_url,
#         "back_id_url": back_id_url,
#         "is_verified": user_detail_instance.is_verified,
#     }




#Email verification, sending otp 'in email
def generate_otp(user):
    # Generate a 6-digit OTP
    totp = pyotp.TOTP(pyotp.random_base32())
    otp = totp.now()
    
    # Set expiration time (10 minutes from now)
    expires_at = datetime.datetime.now() + datetime.timedelta(minutes=10)
    
    # Save OTP to database
    otp_obj = OTPVerification.objects.create(
        user=user,
        otp=otp,
        expires_at=expires_at
    )
    
    return otp

def send_otp_email(user_email, otp):
    subject = 'Email Verification OTP'
    message = f'''Sign-up email code

Thanks for creating an account with FLUX

Here's your authentication code to complete the registration:
Token: {otp}

This code is valid for 10 minutes. Do not share the code with anyone.

Regards,
FLUX team'''
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user_email]
    
    send_mail(subject, message, from_email, recipient_list)
    
def send_otp_email_for_reset_password(user_email, otp):
    subject = 'Reset your FLUX account password'
    message = f'''Reset your FLUX account password

We've received your request to reset the login password for your FLUX account.

Here's your authentication code:

{otp}

This code is valid for 10 minutes, do not share the code with anyone. Not you? Contact customer support immediately to freeze your account.

Regards,
FLUX team'''
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user_email]
    
    send_mail(subject, message, from_email, recipient_list)


def send_password_changed_notification(user_email):
    """
    Sends an email notification to the user that their password has been changed.
    This is a security measure to alert users of account changes.
    """
    subject = 'Your password has changed'
    
    message = f'''You have just changed your FLUX password.

Not you? Contact customer support immediately to freeze your account

Regards,
FLUX team

This is an automated message, please do not reply.'''
    
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user_email]
    
    try:
        send_mail(subject, message, from_email, recipient_list)
        return True
    except Exception as e:
        print(f"Failed to send password change notification: {str(e)}")
        return False

# def generate_reset_token(user):
#     """Generate a secure token for password reset using Django's signer"""
#     signer = TimestampSigner()
#     return signer.sign(str(user.id))

# def verify_reset_token(token, max_age=900):  # 15 minutes in seconds
#     """Verify a password reset token"""
#     signer = TimestampSigner()
#     try:
#         user_id = signer.unsign(token, max_age=max_age)
#         return User.objects.get(id=user_id)
#     except (SignatureExpired, BadSignature, User.DoesNotExist):
#         return None


@router.post('/verify-otp', tags=["User Account"])
def verify_otp(request, data: OTPVerificationSchema):
    try:
        user = User.objects.get(email=data.email)
    except User.DoesNotExist:
        return {"error": "User does not exist"}
    
    # Get the latest OTP for this user
    try:
        otp_obj = OTPVerification.objects.filter(
            user=user, 
            is_used=False
        ).latest('created_at')
    except OTPVerification.DoesNotExist:
        return {"error": "No active OTP found for this user"}
    
    # Verify OTP
    if otp_obj.otp != data.otp:
        return {"error": "Invalid OTP"}
    
    # Check if OTP is expired
    if not otp_obj.is_valid():
        return {"error": "OTP has expired"}
    
    # Mark OTP as used
    otp_obj.is_used = True
    otp_obj.save()
    
    # Activate user and wallet
    user.is_active = True
    user.save()

    wallet = Wallet.objects.get(user_id=user)
    wallet.is_active = True
    wallet.save()
    
    # Now generate JWT token
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
    WALLET_API_URL = "https://apiv2.bhtokens.com/api/v1/user-details"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # You can either send as query parameter
    api_response = requests.post(
        f"{WALLET_API_URL}?apikey={API_KEY}",
        json={
            "uid": user.uid,
            "email":user.email,
            "password":user.password,
            },
        headers=headers
    )

    print(api_response)
    print(user.password)

    # Check if API call was successful
    if api_response.status_code != 200:
        # If API call failed, handle the error but don't delete the user
        # as they've already verified their email
        return {"error": f"Failed to register with wallet service: {api_response.text}"}
    
    cryptocurrencies = Cryptocurrency.objects.all()
    
    return {
        "success": "Email verified successfully! Your account is now active.",
        "user_id": user.id,
        'jwt_token': encoded_token,
        "role": "Client",
        "referral_code": user.referral_code,
        "secret_phrase": user.secret_phrase,
        "uid": user.uid,
        "cryptocurrencies": [crypto.symbol for crypto in cryptocurrencies],
    }

@router.post('/resend-otp', tags=["User Account"])
def resend_otp(request, data: OTPRequestSchema):
    try:
        user = User.objects.get(email=data.email)
    except User.DoesNotExist:
        return {"error": "User does not exist"}
    
    # Check if user is already active
    if user.is_active:
        return {"error": "User is already verified"}
    
    # Generate new OTP
    otp = generate_otp(user)
    
    # Send OTP via email
    send_otp_email(data.email, otp)
    
    return {"message": "OTP resent successfully. Please check your email."}


#Reset Password Functionality
@router.post('/password_reset/request', tags=["User Account"])
def request_password_reset(request, form: OTPRequestSchema):
    #Reset a password by providing an email
    try:
        user = User.objects.get(email=form.email)

        # Generate OTP
        otp = generate_otp(user)
        
        # Send OTP via email
        send_otp_email_for_reset_password(form.email, otp)

        return {"Message": "OTP was successfully sent to your registered email"} 
    except User.DoesNotExist:
        return {"error": "Email does not exist"}

@router.post('/password_reset/verify_otp', tags=["User Account"])
def password_reset_verify_otp(request, forms: OTPVerificationSchema):
    """Verify the OTP sent to email"""
    try:
        user = User.objects.get(email=forms.email)
        otp_obj = OTPVerification.objects.filter(
            user=user, 
            is_used=False
        ).latest('created_at')

        # Verify OTP
        if otp_obj.otp != forms.otp:
            return {"error": "Invalid OTP"}
        
        # Check if OTP is expired
        if not otp_obj.is_valid():
            return {"error": "OTP has expired"}
        
        # Mark OTP as used
        otp_obj.is_used = True
        otp_obj.save()
        
        # Generate a short-lived token for password reset
        # This token will be required in the next step to reset the password
        
        return {
            "success": True, 
            "message": "OTP verified successfully"
        }
        
    except (User.DoesNotExist, OTPVerification.DoesNotExist):
        return {"error": "Invalid OTP or email"}
    

@router.post('/password_reset/resend-otp', tags=["User Account"])
def password_reset_resend_otp(request, data: OTPRequestSchema):
    try:
        user = User.objects.get(email=data.email)
    except User.DoesNotExist:
        return {"error": "User does not exist"}
    
    # Generate new OTP
    otp = generate_otp(user)
    
    # Send OTP via email
    send_otp_email_for_reset_password(data.email, otp)
    
    return {"message": "OTP resent successfully. Please check your email."}

@router.post('/password_reset/reset', tags=["User Account"])
def reset_password(request, forms: ResetPasswordSchema):
    # Check if passwords match
    if forms.new_password != forms.confirm_password:
        return {"error": "Password do not match"} 

    # Validate password strength
    if len(forms.new_password) < 8:
        return {"error": "Password must be at least 8 characters long"}
    elif len(forms.new_password) > 12:
        return {"error": "Password must not exceed 12 characters"}
    
    try:
        user = User.objects.get(email=forms.email)
        
        # Check if new password is the same as the current password
        from django.contrib.auth.hashers import check_password
        if check_password(forms.new_password, user.password):
            return {"error": "New password must differ from previous password"}
        
        # Find the OTP object
        otp_obj = OTPVerification.objects.filter(
            user=user,
            otp=forms.otp,
            is_used=True  # Important: we're looking for the used OTP that was verified
        ).latest('created_at')

        # Update password
        user.password = make_password(forms.new_password)
        user.save()

        send_password_changed_notification(user.email)

        return {
            "success": True, 
            "message": "Password has been reset successfully"
        }
    except User.DoesNotExist:
        return {"error": "User not found"}
    except OTPVerification.DoesNotExist:
        return {"error": "Invalid or expired OTP"} 
    except Exception as e:
        # Log the error but don't expose details to the user
        print(f"Password reset error: {str(e)}")
        return {"error": "Failed to reset password"}
    


#update user country
@router.post("/user-detail/add-country", tags=["User Account"])
def update_selected_country(request, forms: UpdateUserCountry):
    user = User.objects.get(id=forms.user_id)

    user_detail = UserDetail.objects.get(user_id=user)
    user_detail.user_country = forms.country
    user_detail.save()
    
    # Return a response
    return {"status": "success", "message": "Country updated successfully"}

@router.post("/password_reset/verify_current_password", tags=["User Account"])
def verify_reset_password(request, form: PasswordResetSchema):
    try:
        # First, find the user by email
        user = User.objects.get(email=form.email)
        
        # Then verify the password using Django's built-in password verification
        if check_password(form.currentPassword, user.password):
            # Generate OTP
            otp = generate_otp(user)
            
            # Send OTP via email
            send_otp_email_for_reset_password(form.email, otp)

            return {"success": True, "message": "Password matches the email"}
        else:
            return {"error": "Password does not match with the email"}
            
    except ObjectDoesNotExist:
        # User with this email doesn't exist
        return {"error": "Password does not match with the email"}
    except Exception as e:
        # Handle any other unexpected errors
        return {"error": "An error occurred during verification"}

# Email Reset Functionality

def send_otp_email_for_reset_email(user_email, otp):
    """
    Sends an OTP email for email reset verification.
    """
    subject = 'FLUX Email Change Verification'
    message = f'''
    Hello,

    You have requested to change your email address on FLUX.
    
    Your verification code is: {otp}
    
    This code will expire in 15 minutes.
    
    If you did not request this change, please secure your account immediately.
    
    Best regards,
    FLUX Team
    '''
    from_email = 'noreply@flux.com'
    recipient_list = [user_email]
    
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)

def send_email_changed_notification(old_email, new_email):
    """
    Sends a notification email to both old and new email addresses when email is changed.
    This is a security measure to alert users of account changes.
    """
    # Notification to old email
    old_subject = 'FLUX Email Address Changed'
    old_message = f'''
    Hello,

    Your email address on FLUX has been changed from {old_email} to {new_email}.
    
    If you did not make this change, please contact our support team immediately.
    
    Best regards,
    FLUX Team
    '''
    from_email = 'noreply@flux.com'
    
    # Send to old email
    send_mail(old_subject, old_message, from_email, [old_email], fail_silently=False)
    
    # Notification to new email
    new_subject = 'Welcome to FLUX - Email Change Confirmation'
    new_message = f'''
    Hello,

    Your FLUX account email has been successfully changed to this address ({new_email}).
    
    You can now use this email address to log in to your account.
    
    Best regards,
    FLUX Team
    '''
    
    # Send to new email
    send_mail(new_subject, new_message, from_email, [new_email], fail_silently=False)

@router.post("/email_reset/request", tags=["User Account"])
def request_email_reset(request, form: EmailResetSchema):
    try:
        # Find the user by email
        user = User.objects.get(email=form.email)
        
        # Generate OTP
        otp = generate_otp(user)
        
        # Send OTP via email
        send_otp_email_for_reset_email(form.email, otp)

        return {"success": True, "message": "Verification code sent to your email"}
            
    except ObjectDoesNotExist:
        # User with this email doesn't exist
        return {"error": "Email not found"}
    except Exception as e:
        # Handle any other unexpected errors
        return {"error": "An error occurred during verification"}

@router.post('/email_reset/verify_otp', tags=["User Account"])
def email_reset_verify_otp(request, forms: OTPVerificationSchema):
    try:
        # Find the user by email
        user = User.objects.get(email=forms.email)
        
        # Find the most recent OTP for this user that matches the provided OTP
        otp_obj = OTPVerification.objects.filter(
            user=user,
            otp=forms.otp,
            is_used=False  # Must be unused
        ).latest('created_at')
        
        # Check if OTP is valid (not expired)
        if not otp_obj.is_valid():
            return {"error": "OTP has expired. Please request a new one."}
        
        # Mark OTP as used
        otp_obj.is_used = True
        otp_obj.save()
        
        return {
            "success": True, 
            "message": "OTP verified successfully"
        }
        
    except (User.DoesNotExist, OTPVerification.DoesNotExist):
        return {"error": "Invalid OTP or email"}

@router.post('/email_reset/resend_otp', tags=["User Account"])
def email_reset_resend_otp(request, data: OTPRequestSchema):
    try:
        user = User.objects.get(email=data.email)
    except User.DoesNotExist:
        return {"error": "User does not exist"}
    
    # Generate new OTP
    otp = generate_otp(user)
    
    # Send OTP via email
    send_otp_email_for_reset_email(data.email, otp)
    
    return {"message": "OTP resent successfully. Please check your email."}

@router.post('/email_reset/change', tags=["User Account"])
def change_email(request, forms: EmailChangeSchema):
    try:
        # Find the user by current email
        user = User.objects.get(email=forms.email)
        
        # Validate the new email format
        try:
            validate_email(forms.new_email)
        except ValidationError:
            return {"error": "Invalid email format for new email"}
        
        # Check if the new email is already in use
        if User.objects.filter(email=forms.new_email).exists():
            return {"error": "This email is already registered with another account"}
        
        # Find the OTP object
        otp_obj = OTPVerification.objects.filter(
            user=user,
            otp=forms.otp,
            is_used=True  # Important: we're looking for the used OTP that was verified
        ).latest('created_at')
        
        # Store the old email for notification
        old_email = user.email
        
        # Update email
        user.email = forms.new_email
        user.email_verified_at = timezone.now()  # Mark as verified
        user.save()

        # Send notifications to both old and new email addresses
        send_email_changed_notification(old_email, forms.new_email)

        return {
            "success": True, 
            "message": "Email has been changed successfully"
        }
    except User.DoesNotExist:
        return {"error": "User not found"}
    except OTPVerification.DoesNotExist:
        return {"error": "Invalid or expired OTP"} 
    except Exception as e:
        # Log the error but don't expose details to the user
        print(f"Email change error: {str(e)}")
        return {"error": "Failed to change email"}
