from django.db import models
from user_account.models import *
from crypto_currency.models import *
# Create your models here.

class Wallet(models.Model):
    user_id= models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_wallet")
    available_balance=models.DecimalField(max_digits=24,decimal_places=8,default=0)
    wallet_address=models.CharField(max_length=200, null = True, blank = True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user_id

class WalletAddress(models.Model):
    network_id=models.ForeignKey(Network, on_delete=models.CASCADE,null = True, blank = True, related_name='wallet_addresses')
    address=models.CharField(max_length=200, null = True, blank = True)

    def __str__(self):
        return self.address
    
class Transaction(models.Model):
    wallet_id=models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    type=models.CharField(max_length=200, null = True, blank = True)
    amount=models.DecimalField(max_digits=24,decimal_places=8,default=0)
    fee=models.DecimalField(max_digits=24,decimal_places=8,default=0)
    status=models.CharField(max_length=200, null = True, blank = True)

    def __str__(self):
        return self.type

