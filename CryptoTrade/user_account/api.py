from ninja import Router
from .models import *
from .forms import *
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
import random
import string
import secrets

router = Router()

# @router.get('/getUser', response=list[UserSchema])
# def get_user(request):
#     return User.objects.all()

#CREATE
#user registration functionality
@router.post('/signup')
def signup_user(request, form:SingupUserSchema):
    if form.password != form.confirm_password:
        return {"error": "Password do not match!"},
    
    User.objects.create(
        email=form.email,
        password=make_password(form.password),
    )
    return {"success": "The account was successfully signed up!"}

#To generate a code for referral
def RandomReferralCodeGenerator(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

#To generate a secret phrase
def SecretPhraseGenerator(length=12):
    words = string.ascii_letters + string.digits
    return ''.join(secrets.choice(words) for _ in range(length))


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