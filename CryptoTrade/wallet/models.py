from django.db import models
from user_account.models import *
from crypto_currency.models import *
# Create your models here.

class Wallet(models.Model):
    user_id= models.ManyToManyField(User,null = True, blank = True, related_name="user_wallet")
    available_balance=models.DecimalField(max_digits=24,decimal_places=8,default=0)
    wallet_address=models.CharField(max_length=200, null = True, blank = True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user_id

class WalletAddress(models.Model):
    network_id=models.ManyToManyField(Network,null = True, blank = True, related_name='wallet_addresses')
    address=models.CharField(max_length=200, null = True, blank = True)

    def __str__(self):
        return self.address
    
class Transaction(models.Model):
    wallet_id=models.ManyToManyField(Wallet,null = True, blank = True,related_name="transactions")
    type=models.CharField(max_length=200, null = True, blank = True)
    amount=models.DecimalField(max_digits=24,decimal_places=8,default=0)
    fee=models.DecimalField(max_digits=24,decimal_places=8,default=0)
    status=models.CharField(max_length=200, null = True, blank = True)

    def __str__(self):
        return self.type

class WalletBalance(models.Model):
    wallet = models.ForeignKey(Wallet,on_delete=models.CASCADE, null = True, blank = True, related_name='balances')
    cryptocurrency = models.ForeignKey(Cryptocurrency,null = True, blank = True, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=24, decimal_places=8, default=0.0)

    def __str__(self):
        return f"{self.cryptocurrency.symbol}: {self.balance}"