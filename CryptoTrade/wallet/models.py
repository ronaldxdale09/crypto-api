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
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet {self.id}"

class WalletAddress(models.Model):
    network_id = models.ManyToManyField(Network, blank=True, related_name='wallet_addresses')
    address = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, null=True, blank=True, related_name='addresses')

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
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, null=True, blank=True)
    network = models.ForeignKey(Network, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.type} - {self.amount}"

class WalletBalance(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, null=True, blank=True, related_name='balances')
    cryptocurrency = models.ForeignKey(Cryptocurrency, null=True, blank=True, on_delete=models.CASCADE)
    network = models.ForeignKey(Network, null=True, blank=True, on_delete=models.CASCADE, related_name="wallet_network")
    balance = models.DecimalField(max_digits=24, decimal_places=8, default=0.0)
    updated_at = models.DateTimeField(auto_now=True)
    last_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name="affected_balances")

    class Meta:
        unique_together = ('wallet', 'cryptocurrency', 'network')  # Each wallet can have only one balance entry per crypto per network

    def __str__(self):
        crypto_symbol = self.cryptocurrency.symbol if self.cryptocurrency else "Unknown"
        return f"{crypto_symbol}: {self.balance}"

class MarketPrice(models.Model):
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE)
    price_usd = models.DecimalField(max_digits=24, decimal_places=8)
    change_24h = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.cryptocurrency.symbol}: ${self.price_usd}"