from django.db import models
from django.utils import timezone
import datetime

# Create your models here.

class Role(models.Model):
    Role = (
        ('Admin', 'Admin'),
        ('Client', 'Client'),
    )
    role = models.CharField(max_length=200, null = True, blank = True)

    def __str__(self):
        return self.role
    
class User(models.Model):
    name = models.CharField(max_length=200, null = True, blank = True)
    email = models.EmailField(max_length=200, null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    password = models.CharField(max_length=200, null=True, blank=True)
    role_id=models.ManyToManyField(Role,null = True, blank = True )
    jwt_token = models.TextField(null = True, blank = True)
    uid=models.CharField(max_length=200, null = True, blank = True)
    referral_code=models.CharField(max_length=200, null = True, blank = True)
    secret_phrase=models.CharField(max_length=200, null = True, blank = True)
    is_active = models.BooleanField(default=False)
    # def __str__(self):
    #     return self.name
    
class UserDetail(models.Model):
    user_profile = models.TextField(null=True, blank=True) 
    user_id= models.OneToOneField(User,null = True, blank = True, on_delete=models.CASCADE)
    phone_number= models.CharField(max_length=200, null = True, blank = True)
    is_verified=models.BooleanField(default=False)
    tier=models.BooleanField(default=False)
    trading_fee_rate=models.CharField(max_length=200, null = True, blank = True)
    last_login_session=models.CharField(max_length=200, null = True, blank = True)
    ip_address = models.CharField(max_length=200, null=True, blank=True)  # Temporarily use CharField
    previous_ip_address = models.CharField(max_length=200, null=True, blank=True)  # Temporarily use CharField
    status=models.CharField(max_length=200, null = True, blank = True)
   

    def __str__(self):
        return self.user_id

class KnowYourCustomer(models.Model):
    DOCUMENT_TYPES = [
        ('drivers_license', 'drivers license'),
        ('national_id', 'National ID Card'),
        ('passport', 'Passport'),
        ('umid', 'Unified Multi-Purpose ID'),
        ('postal_id', 'Postal ID'),
        ('prc_id', 'PRC ID'),
    ]

    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('unverified', 'Unverified')
    ]
    
    user_id= models.OneToOneField(User, on_delete=models.CASCADE)
    kyc_level=models.CharField(max_length=200, null = True, blank = True)
    full_name=models.CharField(max_length=200, null = True, blank = True)
    address=models.CharField(max_length=200, null = True, blank = True)
    document_type=models.CharField(max_length=200, null = True, blank = True)
    document_number=models.CharField(max_length=200, null = True, blank = True)
    verification_status=models.CharField(max_length=200, null = True, blank = True)
    street=models.CharField(max_length=200, null = True, blank = True)
    city=models.CharField(max_length=200, null = True, blank = True)
    country=models.CharField(max_length=200, null = True, blank = True)
    postal_code=models.CharField(max_length=200, null = True, blank = True)
    captured_selfie= models.TextField(null=True, blank=True)
    back_captured_image=models.TextField(null=True, blank=True)
    front_captured_image=models.TextField(null=True, blank=True)
    # uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
    
class Address(models.Model):
    address_type=models.CharField(max_length=200, null = True, blank = True) #Example is TRC20
    address = models.CharField(max_length=200, null = True, blank = True) # TAL9AnPR35ogDy53sgpcLyEL9nASy2m4z

    def __str__(self):
        return self.address
    
class UserAddress(models.Model):
    user_id = models.ManyToManyField(User,null = True, blank = True)
    address_id = models.ManyToManyField(Address,null = True, blank = True)

class OTPVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"OTP for {self.user.email}"
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
