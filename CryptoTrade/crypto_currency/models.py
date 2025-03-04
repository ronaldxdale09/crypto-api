# crypto_currency/models.py - Updated with Network Relationships

from django.db import models
from django.utils import timezone

class Network(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    website = models.URLField(blank=True)
    api_key = models.CharField(max_length=200, null=True, blank=True)
    network_description = models.CharField(max_length=200, null=True, blank=True)
    acronym = models.CharField(max_length=200, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    logo_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

class Cryptocurrency(models.Model):
    symbol = models.CharField(max_length=20, null=True, blank=True)
    id_pk = models.CharField(max_length=50, unique=True)  # For API identifiers
    name = models.CharField(max_length=100, null=True, blank=True)
    is_tradable = models.BooleanField(default=True)
    crypto_description = models.CharField(max_length=200, null=True, blank=True)
    price = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    price_change_24h = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    market_cap = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)
    volume_24h = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    logo_url = models.URLField(blank=True, null=True)
    logo_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.symbol or self.name

class CryptocurrencyNetwork(models.Model):
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='networks')
    network = models.ForeignKey(Network, on_delete=models.CASCADE)
    is_deposit_enabled = models.BooleanField(default=True)
    is_withdrawal_enabled = models.BooleanField(default=True)
    withdrawal_fee = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    min_withdrawal = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    deposit_confirmations = models.IntegerField(default=6)
    
    class Meta:
        unique_together = ('cryptocurrency', 'network')
        
    def __str__(self):
        return f"{self.cryptocurrency.symbol} on {self.network.name}"
        
class PriceHistory(models.Model):
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='price_history')
    timestamp = models.DateTimeField()
    price = models.DecimalField(max_digits=24, decimal_places=8)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.cryptocurrency.symbol} - {self.timestamp}"