from ninja import Router
from typing import List
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from user_account.models import User
from crypto_currency.models import Cryptocurrency
from wallet.models import Wallet, WalletBalance
from .models import Order, Trade, TradingPair
from .forms import *

router = Router()

# Trading Pairs
@router.get('/pairs', response=TradingPairListResponseSchema)
def get_trading_pairs(request):
    """Get all available trading pairs."""
    pairs = TradingPair.objects.filter(is_active=True)
    
    result = []
    for pair in pairs:
        result.append({
            "id": pair.id,
            "base_currency_id": pair.base_currency.id,
            "quote_currency_id": pair.quote_currency.id,
            "base_symbol": pair.base_currency.symbol,
            "quote_symbol": pair.quote_currency.symbol,
            "is_active": pair.is_active
        })
    
    return {
        "pairs": result,
        "count": len(result)
    }

# Market Data
@router.get('/market/{pair_id}', response=MarketDataSchema)
def get_market_data(request, pair_id: int):
    """Get market data for a trading pair."""
    pair = get_object_or_404(TradingPair, id=pair_id)
    
    # In a real app, you would calculate these from your order book and trade history
    # This is mock data for demonstration
    return {
        "pair_id": pair.id,
        "pair_name": f"{pair.base_currency.symbol}/{pair.quote_currency.symbol}",
        "current_price": Decimal('42500.25'),
        "high_24h": Decimal('43200.00'),
        "low_24h": Decimal('41800.75'),
        "volume_24h": Decimal('2543.25'),
        "change_24h": Decimal('-0.58')
    }

# Orders
@router.post('/order', response=OrderResponseSchema)
def create_order(request, form: CreateOrderSchema):
    """Create a buy or sell order."""
    user = get_object_or_404(User, id=form.user_id)
    wallet = get_object_or_404(Wallet, id=form.wallet_id)
    crypto = get_object_or_404(Cryptocurrency, id=form.crypto_id)
    
    # Validate order type
    if form.order_type not in ['buy', 'sell']:
        return {"success": False, "error": "Invalid order type"}
    
    # Check if user has sufficient balance
    try:
        if form.order_type == 'buy':
            # For buy orders, check if user has enough quote currency (e.g., USDT)
            # This is simplified - in a real app you would identify the quote currency
            total_cost = form.price * form.amount
            if wallet.available_balance < total_cost:
                return {"success": False, "error": "Insufficient balance"}
        else:  # sell
            # For sell orders, check if user has enough of the cryptocurrency
            wallet_balance = WalletBalance.objects.get(wallet=wallet, cryptocurrency=crypto)
            if wallet_balance.balance < form.amount:
                return {"success": False, "error": "Insufficient cryptocurrency balance"}
    except WalletBalance.DoesNotExist:
        return {"success": False, "error": "No balance found for this cryptocurrency"}
    
    # Create the order
    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            wallet=wallet,
            cryptocurrency=crypto,
            order_type=form.order_type,
            price=form.price,
            amount=form.amount,
            status='pending'
        )
        
        # In a real app, you would:
        # 1. Reserve the funds/crypto
        # 2. Try to match with existing orders
        # 3. Create trades for matched orders
        
        # For demo purposes, we'll just create the order
        
    return {
        "success": True,
        "order": {
            "id": order.id,
            "user_id": order.user.id,
            "wallet_id": order.wallet.id,
            "crypto_id": order.cryptocurrency.id,
            "order_type": order.order_type,
            "price": order.price,
            "amount": order.amount,
            "status": order.status,
            "created_at": order.created_at,
            "completed_at": order.completed_at
        }
    }

@router.post('/order/{order_id}/cancel')
def cancel_order(request, order_id: int, form: CancelOrderSchema):
    """Cancel a pending order."""
    order = get_object_or_404(Order, id=order_id)
    
    # Security check - ensure the user owns this order
    if order.user.id != form.user_id:
        return {"success": False, "error": "Unauthorized"}
    
    # Check if the order can be cancelled
    if order.status != 'pending':
        return {"success": False, "error": f"Cannot cancel order in {order.status} state"}
    
    with transaction.atomic():
        order.status = 'cancelled'
        order.save()
        
        # In a real app, you would release any reserved funds here
        
    return {
        "success": True,
        "order_id": order.id,
        "status": order.status
    }

@router.get('/orders/{user_id}', response=OrderListResponseSchema)
def get_user_orders(request, user_id: int, status: str = None):
    """Get all orders for a user, optionally filtered by status."""
    user = get_object_or_404(User, id=user_id)
    
    query = Q(user=user)
    if status:
        query &= Q(status=status)
    
    orders = Order.objects.filter(query).order_by('-created_at')
    
    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "user_id": order.user.id,
            "wallet_id": order.wallet.id,
            "crypto_id": order.cryptocurrency.id,
            "order_type": order.order_type,
            "price": order.price,
            "amount": order.amount,
            "status": order.status,
            "created_at": order.created_at,
            "completed_at": order.completed_at
        })
    
    return {
        "orders": result,
        "count": len(result)
    }

@router.get('/trades/{user_id}', response=TradeListResponseSchema)
def get_user_trades(request, user_id: int):
    """Get trade history for a user."""
    user = get_object_or_404(User, id=user_id)
    
    # Get all trades where the user is either the buyer or seller
    trades = Trade.objects.filter(
        Q(buyer=user) | Q(seller=user)
    ).order_by('-executed_at')
    
    result = []
    for trade in trades:
        result.append({
            "id": trade.id,
            "buyer_id": trade.buyer.id,
            "seller_id": trade.seller.id,
            "crypto_id": trade.cryptocurrency.id,
            "price": trade.price,
            "amount": trade.amount,
            "fee": trade.fee,
            "executed_at": trade.executed_at
        })
    
    return {
        "trades": result,
        "count": len(result)
    }

# Simple buy and sell functions for direct transactions
@router.post('/buy')
def buy_crypto(request, user_id: int, crypto_id: int, amount: Decimal):
    """
    Buy cryptocurrency directly at market price.
    This is a simplified version for FlutterFlow integration.
    """
    user = get_object_or_404(User, id=user_id)
    crypto = get_object_or_404(Cryptocurrency, id=crypto_id)
    
    # Find the user's wallet
    try:
        wallet = Wallet.objects.get(user_id=user)
    except Wallet.DoesNotExist:
        return {"success": False, "error": "Wallet not found"}
    
    # Get current price (in a real app, this would come from an exchange API)
    current_price = Decimal('42500.00')  # Example price
    
    # Calculate total cost
    total_cost = amount * current_price
    
    # Check if user has enough balance
    if wallet.available_balance < total_cost:
        return {"success": False, "error": "Insufficient balance"}
    
    with transaction.atomic():
        # Create an order
        order = Order.objects.create(
            user=user,
            wallet=wallet,
            cryptocurrency=crypto,
            order_type='buy',
            price=current_price,
            amount=amount,
            status='completed',
            completed_at=timezone.now()
        )
        
        # Create a trade record
        trade = Trade.objects.create(
            buyer=user,
            seller=None,  # In a real exchange, this would be the matched seller
            cryptocurrency=crypto,
            buy_order=order,
            sell_order=None,
            price=current_price,
            amount=amount,
            fee=total_cost * Decimal('0.001')  # 0.1% fee example
        )
        
        # Update wallet balances
        wallet.available_balance -= total_cost
        wallet.save()
        
        # Update or create crypto balance
        crypto_balance, created = WalletBalance.objects.get_or_create(
            wallet=wallet,
            cryptocurrency=crypto,
            defaults={"balance": 0}
        )
        crypto_balance.balance += amount
        crypto_balance.save()
    
    return {
        "success": True,
        "order_id": order.id,
        "trade_id": trade.id,
        "price": current_price,
        "amount": amount,
        "total_cost": total_cost,
        "fee": trade.fee
    }

@router.post('/sell')
def sell_crypto(request, user_id: int, crypto_id: int, amount: Decimal):
    """
    Sell cryptocurrency directly at market price.
    This is a simplified version for FlutterFlow integration.
    """
    user = get_object_or_404(User, id=user_id)
    crypto = get_object_or_404(Cryptocurrency, id=crypto_id)
    
    # Find the user's wallet
    try:
        wallet = Wallet.objects.get(user_id=user)
    except Wallet.DoesNotExist:
        return {"success": False, "error": "Wallet not found"}
    
    # Check if user has enough crypto
    try:
        crypto_balance = WalletBalance.objects.get(wallet=wallet, cryptocurrency=crypto)
        if crypto_balance.balance < amount:
            return {"success": False, "error": "Insufficient cryptocurrency balance"}
    except WalletBalance.DoesNotExist:
        return {"success": False, "error": "No balance found for this cryptocurrency"}
    
    # Get current price (in a real app, this would come from an exchange API)
    current_price = Decimal('42500.00')  # Example price
    
    # Calculate total value
    total_value = amount * current_price
    
    with transaction.atomic():
        # Create an order
        order = Order.objects.create(
            user=user,
            wallet=wallet,
            cryptocurrency=crypto,
            order_type='sell',
            price=current_price,
            amount=amount,
            status='completed',
            completed_at=timezone.now()
        )
        
        # Create a trade record
        trade = Trade.objects.create(
            buyer=None,  # In a real exchange, this would be the matched buyer
            seller=user,
            cryptocurrency=crypto,
            buy_order=None,
            sell_order=order,
            price=current_price,
            amount=amount,
            fee=total_value * Decimal('0.001')  # 0.1% fee example
        )
        
        # Update wallet balances
        crypto_balance.balance -= amount
        crypto_balance.save()
        
        # Add the value to wallet balance (minus fee)
        fee_amount = total_value * Decimal('0.001')
        wallet.available_balance += (total_value - fee_amount)
        wallet.save()
    
    return {
        "success": True,
        "order_id": order.id,
        "trade_id": trade.id,
        "price": current_price,
        "amount": amount,
        "total_value": total_value,
        "fee": fee_amount
    }