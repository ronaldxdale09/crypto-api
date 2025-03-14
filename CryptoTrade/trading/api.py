from ninja import Router
from typing import List
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from user_account.models import User
from crypto_currency.models import Cryptocurrency
from wallet.models import Wallet, UserAsset
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
    """Create a buy or sell order (market or limit)."""
    user = get_object_or_404(User, id=form.user_id)
    wallet = get_object_or_404(Wallet, id=form.wallet_id)
    crypto = get_object_or_404(Cryptocurrency, id=form.crypto_id)
    
    # Validate order type
    if form.order_type not in ['buy', 'sell']:
        return {"success": False, "error": "Invalid order type"}
    
    # Validate order execution type (market or limit)
    if form.execution_type not in ['market', 'limit']:
        return {"success": False, "error": "Invalid execution type"}

    try:
        if form.order_type == 'buy':
            total_cost = form.price * form.amount if form.execution_type == 'limit' else form.amount
            if wallet.available_balance < total_cost:
                return {"success": False, "error": "Insufficient balance"}
        else:  # sell
            wallet_balance = UserAsset.objects.get(wallet=wallet, cryptocurrency=crypto)
            if wallet_balance.balance < form.amount:
                return {"success": False, "error": "Insufficient cryptocurrency balance"}
    except UserAsset.DoesNotExist:
        return {"success": False, "error": "No balance found for this cryptocurrency"}
    
    # Create the order
    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            wallet=wallet,
            cryptocurrency=crypto,
            order_type=form.order_type,
            execution_type=form.execution_type,
            price=form.price if form.execution_type == 'limit' else None,
            amount=form.amount,
            status='pending'
        )
    
    return {
        "success": True,
        "order": {
            "id": order.id,
            "user_id": order.user.id,
            "wallet_id": order.wallet.id,
            "crypto_id": order.cryptocurrency.id,
            "order_type": order.order_type,
            "execution_type": order.execution_type,
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


@router.get('/order/user={user_id}', tags=["Trading"])
def get_user_orders(request, user_id: int):
    # Get user instance
        user_instance = User.objects.get(id=user_id)

        # Get wallet associated with the user
        wallet_instance = Wallet.objects.get(user_id=user_instance.id)

        # Get all orders for the wallet
        orders = Order.objects.filter(wallet=wallet_instance).order_by('-created_at')

        # Serialize orders
        result = [
            {
                "id": order.id,
                "user_id": order.user.id,
                "wallet_id": order.wallet.id,
                "crypto_id": order.cryptocurrency.id,
                "order_type": order.order_type,
                "execution_type": order.execution_type,
                "price": str(order.price),
                "amount": str(order.amount),
                "status": order.status,
                "created_at": order.created_at.isoformat(),
                "completed_at": order.completed_at.isoformat() if order.completed_at else None,
                "is_approved": order.is_approved,
                "is_declined": order.is_declined,
            }
            for order in orders
        ]

        return {"orders": result, "count": len(result)}

@router.get('/trades/{user_id}', response=TradeListResponseSchema, tags=["Trading"])
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


@router.post('/trading/buy/{user_id}/{crypto_id}', tags=["Trading"])
def buy_crypto(request, user_id: int, crypto_id: int, currentPrice: float, totalAmount: float):
    """
    Buy cryptocurrency directly at market price.
    
    Path parameters:
    - user_id: ID of the user making the purchase
    - crypto_id: ID of the cryptocurrency to buy
    
    Query parameters:
    - currentPrice: Current price of the cryptocurrency
    - totalAmount: Total amount in USD to spend
    
    Example: /api/trading/buy/1/2?currentPrice=42500.00&totalAmount=500.00
    """
    try:
        # Convert numeric values to Decimal for precision
        current_price = Decimal(str(currentPrice))
        total_amount = Decimal(str(totalAmount))
        
        # Validate values are positive
        if current_price <= 0:
            return {"success": False, "error": "Price must be greater than zero"}
        if total_amount <= 0:
            return {"success": False, "error": "Amount must be greater than zero"}
        
        # Get user and cryptocurrency
        user = get_object_or_404(User, id=user_id)
        crypto = get_object_or_404(Cryptocurrency, id=crypto_id)
        
        # Find the user's wallet
        try:
            wallet = Wallet.objects.get(user_id=user.id)
        except Wallet.DoesNotExist:
            return {"success": False, "error": "Wallet not found"}
        
        # Calculate coin amount based on total USD amount and price
        coin_amount = total_amount / current_price
        
        # Calculate fee
        fee = total_amount * Decimal('0.001')  # 0.1% fee example
        total_with_fee = total_amount + fee
        
        # Check if user has enough balance
        if wallet.available_balance < total_with_fee:
            return {"success": False, "error": "Insufficient balance"}
        
        try:
            with transaction.atomic():
                # Create the order -
                order = Order(
                    user=user,
                    wallet=wallet,
                    cryptocurrency=crypto,
                    order_type='buy',
                    price=current_price,
                    amount=coin_amount,
                    status='completed',
                    completed_at=timezone.now(),
                    is_approved=True,
                    is_declined=False
                )
                order.save()
                
                # Insert trade record directly using raw SQL to bypass ORM constraints
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO trading_trade 
                        (price, amount, fee, executed_at, buyer_id, cryptocurrency_id, buy_order_id, sell_order_id) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        [
                            current_price, coin_amount, fee, timezone.now(), user.id, 
                            crypto.id, order.id, None
                        ]
                    )
                    trade_id = cursor.fetchone()[0]
                
                # Update wallet balances
                wallet.available_balance -= total_with_fee
                wallet.save()
                
                # Update or create crypto balance
                crypto_balance, created = UserAsset.objects.get_or_create(
                    wallet=wallet,
                    cryptocurrency=crypto,
                    defaults={"balance": 0}
                )
                crypto_balance.balance += coin_amount
                crypto_balance.save()
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        return {
            "success": True,
            "order_id": order.id,
            "trade_id": trade_id,
            "price": current_price,
            "coin_amount": coin_amount,
            "total_amount": total_amount,
            "fee": fee
        }
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

@router.post('/trading/sell/{user_id}/{crypto_id}', tags=["Trading"])
def sell_crypto(request, user_id: int, crypto_id: int, currentPrice: float, amount: float):
    """
    Sell cryptocurrency at market price.
    
    Path parameters:
    - user_id: ID of the user selling
    - crypto_id: ID of the cryptocurrency to sell
    
    Query parameters:
    - currentPrice: Current price of the cryptocurrency
    - amount: Amount in coins to sell
    
    Example: /api/trading/sell/1/2?currentPrice=42500.00&amount=0.5
    """
    try:
        # Convert numeric values to Decimal for precision
        current_price = Decimal(str(currentPrice))
        coin_amount = Decimal(str(amount))
        
        # Validate values are positive
        if current_price <= 0:
            return {"success": False, "error": "Price must be greater than zero"}
        if coin_amount <= 0:
            return {"success": False, "error": "Amount must be greater than zero"}
        
        # Get user and cryptocurrency
        user = get_object_or_404(User, id=user_id)
        crypto = get_object_or_404(Cryptocurrency, id=crypto_id)
        
        # Find the user's wallet
        try:
            wallet = Wallet.objects.get(user_id=user.id)
        except Wallet.DoesNotExist:
            return {"success": False, "error": "Wallet not found"}
        
        # Check if user has enough crypto
        try:
            crypto_balance = UserAsset.objects.get(wallet=wallet, cryptocurrency=crypto)
            if crypto_balance.balance < coin_amount:
                return {"success": False, "error": "Insufficient cryptocurrency balance"}
        except UserAsset.DoesNotExist:
            return {"success": False, "error": "No balance found for this cryptocurrency"}
        
        # Calculate total value
        total_value = coin_amount * current_price
        fee = total_value * Decimal('0.001')  # 0.1% fee example
        
        try:
            with transaction.atomic():
                # Create the order - without execution_type
                order = Order(
                    user=user,
                    wallet=wallet,
                    cryptocurrency=crypto,
                    order_type='sell',
                    price=current_price,
                    amount=coin_amount,
                    status='completed',
                    completed_at=timezone.now(),
                    is_approved=True,
                    is_declined=False
                )
                order.save()
                
                # Insert trade record directly using raw SQL to bypass ORM constraints
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO trading_trade 
                        (price, amount, fee, executed_at, buyer_id, cryptocurrency_id, buy_order_id, sell_order_id) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        [
                            current_price, coin_amount, fee, timezone.now(), user.id, 
                            crypto.id, None, order.id
                        ]
                    )
                    trade_id = cursor.fetchone()[0]
                
                # Update wallet balances
                crypto_balance.balance -= coin_amount
                crypto_balance.save()
                
                # Add the value to wallet balance (minus fee)
                wallet.available_balance += (total_value - fee)
                wallet.save()
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        return {
            "success": True,
            "order_id": order.id,
            "trade_id": trade_id,
            "price": current_price,
            "amount": coin_amount,
            "total_value": total_value,
            "fee": fee
        }
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}