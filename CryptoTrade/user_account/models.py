from django.db import models
from django.utils import timezone


# Create your models here.

class Role(models.Model):
    role_name = models.CharField(max_length=200, null = True, blank = True)

    def __str__(self):
        return self.role_name
    
class User(models.Model):
    name = models.CharField(max_length=200, null = True, blank = True)
    email = models.EmailField(max_length=200, null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True, default=timezone.now)
    password = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name
    
class UserDetail(models.Model):
    user_id= models.OneToOneField(User,null = True, blank = True, on_delete=models.CASCADE)
    role_id=models.ManyToManyField(Role,null = True, blank = True )
    phone_number= models.CharField(max_length=200, null = True, blank = True)
    secret_phrase=models.CharField(max_length=200, null = True, blank = True)
    is_verified=models.BooleanField(default=False)
    tier=models.BooleanField(default=False)
    trading_fee_rate=models.CharField(max_length=200, null = True, blank = True)
    ip_address=models.CharField(max_length=200, null = True, blank = True)
    last_login_session=models.CharField(max_length=200, null = True, blank = True)
    previous_ip_address=models.CharField(max_length=200, null = True, blank = True)
    referral_code=models.CharField(max_length=200, null = True, blank = True)
    status=models.CharField(max_length=200, null = True, blank = True)

    def __str__(self):
        return self.user_id

class KnowYourCustomer(models.Model):
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

