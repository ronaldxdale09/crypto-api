from django.db import models
from django.utils import timezone
from user_account.models import User
from crypto_currency.models import Cryptocurrency


class Order(models.Model):
    TYPE_CHOICES = (
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    )

    EXECUTION_TYPE = (
        ('market', 'Market'),
        ('limit', 'Limit')
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    execution_type = models.CharField(max_length=10, choices=EXECUTION_TYPE, default='limit')
    price = models.DecimalField(max_digits=24, decimal_places=8)
    amount = models.DecimalField(max_digits=24, decimal_places=8)
    total_in_usdt = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    trade_fee = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    external_order_id = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.order_type.capitalize()} {self.amount} {self.cryptocurrency.symbol} @ {self.price}"
    
    
class Trade(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases', null=True, blank=True)
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='trades')
    buy_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='buy_trade', null=True)
    sell_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='sell_trade', null=True)
    price = models.DecimalField(max_digits=24, decimal_places=8)
    amount = models.DecimalField(max_digits=24, decimal_places=8)
    fee = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    executed_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Trade: {self.amount} {self.cryptocurrency.symbol} @ {self.price}"

class TradingPair(models.Model):
    base_currency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='base_pairs')
    quote_currency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='quote_pairs')
    is_active = models.BooleanField(default=True)
    external_pair_id = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ('base_currency', 'quote_currency')
    
    def __str__(self):
        return f"{self.base_currency.symbol}/{self.quote_currency.symbol}"