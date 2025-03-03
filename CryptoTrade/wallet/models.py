from django.db import models
from user_account.models import *
from crypto_currency.models import *
from django.utils import timezone

# Create your models here.

class Wallet(models.Model):
    user_id = models.ManyToManyField(User, blank=True, related_name="user_wallet")
    available_balance = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    wallet_address = models.CharField(max_length=200, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)  # Changed from auto_now_add
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet {self.id}"

class WalletAddress(models.Model):
    network_id = models.ManyToManyField(Network, blank=True, related_name='wallet_addresses')
    address = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)  # Changed from auto_now_add

    def __str__(self):
        return self.address
    
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
        ('transfer', 'Transfer'),
    )
    
    TRANSACTION_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    wallet_id = models.ManyToManyField(Wallet, blank=True, related_name="transactions")
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, null=True, blank=True)
    amount = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    fee = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    tx_hash = models.CharField(max_length=200, null=True, blank=True)
    destination_address = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.type} - {self.amount}"

class WalletBalance(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, null=True, blank=True, related_name='balances')
    cryptocurrency = models.ForeignKey(Cryptocurrency, null=True, blank=True, on_delete=models.CASCADE)
    network = models.ForeignKey(Network, null=True, blank=True, on_delete=models.CASCADE, related_name="wallet_network")
    balance = models.DecimalField(max_digits=24, decimal_places=8, default=0.0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cryptocurrency.symbol}: {self.balance}"