from ninja import Router
from typing import List
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
import requests 
from user_account.models import User
from crypto_currency.models import Cryptocurrency
from wallet.models import Wallet, UserAsset
from .models import Order, Trade, TradingPair
from .forms import *



router = Router()

ORDER_API_URL = "https://wallet-app-api-main-m41zlt.laravel.cloud/api/v1/orders"
WALLET_API_URL = "https://wallet-app-api-main-m41zlt.laravel.cloud/api/v1/user-wallets"
API_KEY = "A20RqFwVktRxxRqrKBtmi6ud"

def create_external_order(order_data):
    """
    Create an order using the external API.
    
    Args:
        order_data (dict): Order data containing:
            - uid: User identifier
            - coin_pair_id: Coin pair identifier
            - wallet_id: Wallet identifier
            - order_type: 'buy' or 'sell'
            - excecution_type: 'market' or 'limit'
            - price: Order price
            - amount: Order amount
            - total_in_usdt: Total order value in USDT
    
    Returns:
        dict: {
            'success': bool,
            'order_data': dict or None,
            'order_id': str or None,
            'error': str or None
        }
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Add API key to the order data
    payload = {
        'apikey': API_KEY,
        **order_data
    }
    
    try:
        api_response = requests.post(
            ORDER_API_URL,
            json=payload,
            headers=headers,
            timeout=10  # Set timeout to avoid hanging requests
        )
        
        # Check if request was successful
        if api_response.status_code not in (200, 201):
            return {
                'success': False,
                'order_data': None,
                'order_id': None,
                'error': f"API request failed with status code: {api_response.status_code}. Response: {api_response.text}"
            }
        
        # Parse response data
        response_data = api_response.json()
        
        # Check if order data exists in response
        if not response_data or not isinstance(response_data, dict):
            return {
                'success': False,
                'order_data': None,
                'order_id': None,
                'error': "Invalid response format from API"
            }
        
        # Extract order ID or relevant data
        order_id = response_data.get('order_id')
        
        return {
            'success': True,
            'order_data': response_data,
            'order_id': order_id,
            'error': None
        }
    
    except requests.RequestException as e:
        # Handle network-related errors
        return {
            'success': False,
            'order_data': None,
            'order_id': None,
            'error': f"Network error: {str(e)}"
        }
    except (ValueError, KeyError, TypeError) as e:
        # Handle data parsing errors
        return {
            'success': False,
            'order_data': None,
            'order_id': None,
            'error': f"Data parsing error: {str(e)}"
        }
    except Exception as e:
        # Handle any other unexpected errors
        return {
            'success': False,
            'order_data': None,
            'order_id': None,
            'error': f"Unexpected error: {str(e)}"
        }
    


def get_user_wallet(uid):
    """
    Get user wallet information from the external wallet API.
    
    Args:
        uid (str): User identifier
        
    Returns:
        dict: {
            'success': bool,
            'wallet_data': list or None,
            'spot_balance': Decimal or None,
            'error': str or None
        }
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        api_response = requests.get(
            f"{WALLET_API_URL}/{uid}?apikey={API_KEY}",
            headers=headers,
            timeout=10  # Set timeout to avoid hanging requests
        )
        
        # Check if request was successful
        if api_response.status_code != 200:
            return {
                'success': False,
                'wallet_data': None,
                'spot_balance': None,
                'error': f"API request failed with status code: {api_response.status_code}"
            }
        
        # Parse wallet data
        wallet_data = api_response.json()
        
        # Check if wallet data exists
        if not wallet_data or not isinstance(wallet_data, list) or len(wallet_data) == 0:
            return {
                'success': False,
                'wallet_data': None,
                'spot_balance': None,
                'error': "No wallet data found"
            }
        
        # Extract spot wallet balance
        spot_wallet_balance = Decimal(wallet_data[0]['spot_wallet'])
        
        return {
            'success': True,
            'wallet_data': wallet_data,
            'spot_balance': spot_wallet_balance,
            'error': None
        }
    
    except requests.RequestException as e:
        # Handle network-related errors
        return {
            'success': False,
            'wallet_data': None,
            'spot_balance': None,
            'error': f"Network error: {str(e)}"
        }
    except (ValueError, KeyError, TypeError) as e:
        # Handle data parsing errors
        return {
            'success': False,
            'wallet_data': None,
            'spot_balance': None,
            'error': f"Data parsing error: {str(e)}"
        }
    except Exception as e:
        # Handle any other unexpected errors
        return {
            'success': False,
            'wallet_data': None,
            'spot_balance': None,
            'error': f"Unexpected error: {str(e)}"
        }




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

# Orders@router.post('/order', response=OrderResponseSchema)
def create_order(request, form: CreateOrderSchema):
    """Create a buy or sell order (market or limit)."""
    try:
        user = get_object_or_404(User, id=form.user_id)
        wallet = get_object_or_404(Wallet, id=form.wallet_id)
        crypto = get_object_or_404(Cryptocurrency, id=form.crypto_id)
        
        # Validate order type
        if form.order_type not in ['buy', 'sell']:
            return {"success": False, "error": "Invalid order type"}
        
        # Validate order execution type (market or limit)
        if form.execution_type not in ['market', 'limit']:
            return {"success": False, "error": "Invalid execution type"}

        # Calculate total amount in USDT
        if form.execution_type == 'limit':
            total_in_usdt = form.price * form.amount
        else:  # market order
            total_in_usdt = form.amount  # For market orders, amount is total USDT value
        
        # For buy orders, check if user has enough balance
        if form.order_type == 'buy':
            wallet_result = get_user_wallet(user.uid)
            if not wallet_result['success']:
                return {"success": False, "error": wallet_result['error']}
                
            spot_wallet_balance = wallet_result['spot_balance']
            if spot_wallet_balance < total_in_usdt:
                return {"success": False, "error": "Insufficient balance in spot wallet"}
                
        # For sell orders, check if user has enough of the cryptocurrency
        else:  # sell
            try:
                wallet_balance = UserAsset.objects.get(cryptocurrency=crypto)
                if wallet_balance.balance < form.amount:
                    return {"success": False, "error": "Insufficient cryptocurrency balance"}
            except UserAsset.DoesNotExist:
                return {"success": False, "error": "No balance found for this cryptocurrency"}
        
        # Prepare data for external API call
        order_data = {
            'uid': user.uid,
            'coin_pair_id': crypto.external_id,  # Assuming the cryptocurrency has an external_id field
            'wallet_id': wallet.external_id,  # Assuming the wallet has an external_id field
            'order_type': form.order_type,
            'excecution_type': form.execution_type,
            'price': float(form.price) if form.execution_type == 'limit' else 0,
            'amount': float(form.amount),
            'total_in_usdt': float(total_in_usdt)
        }
        
        # Call external API to create order
        api_result = create_external_order(order_data)
        
        if not api_result['success']:
            return {"success": False, "error": api_result['error']}
        
        # Create local record of the order
        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                wallet=wallet,
                cryptocurrency=crypto,
                order_type=form.order_type,
                execution_type=form.execution_type,
                price=form.price if form.execution_type == 'limit' else None,
                amount=form.amount,
                status='pending',
                external_order_id=api_result['order_id']  # Store the external order ID
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
                "completed_at": order.completed_at,
                "external_order_id": order.external_order_id
            }
        }
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

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

        # Calculate coin amount based on total USD amount and price
        coin_amount = total_amount / current_price
        
        # Get user wallet data using the reusable function
        wallet_result = get_user_wallet(user.uid)
        if not wallet_result['success']:
            return {"success": False, "error": wallet_result['error']}

        wallet_data = wallet_result['wallet_data']
        spot_wallet_balance = wallet_result['spot_balance']
        wallet_id = wallet_data[0]['id']  # Get wallet ID from external API
        
        # Calculate fee
        fee = total_amount * Decimal('0.001')  # 0.1% fee example
        total_with_fee = total_amount + fee

        # Check if there's enough balance in spot wallet
        if spot_wallet_balance < total_with_fee:
            return {"success": False, "error": "Insufficient spot wallet balance"}
        
        # Prepare data for external order API
        order_data = {
            'uid': user.uid,
            'coin_pair_id': crypto.external_id,  # Assuming crypto has external_id field
            'wallet_id': wallet_id,
            'order_type': 'buy',
            'excecution_type': 'market',  # Market order
            'price': float(current_price),
            'amount': float(coin_amount),
            'total_in_usdt': float(total_amount)
        }
        
        # Call external API to create order
        api_result = create_external_order(order_data)
        if not api_result['success']:
            return {"success": False, "error": api_result['error']}
            
        external_order_id = api_result['order_id']
        
        try:
            with transaction.atomic():
                # Create local order record
                order = Order(
                    user=user,
                    cryptocurrency=crypto,
                    order_type='buy',
                    execution_type='market',
                    price=current_price,
                    amount=coin_amount,
                    status='completed',
                    completed_at=timezone.now(),
                    is_approved=True,
                    is_declined=False,
                    external_order_id=external_order_id
                )
                order.save()
                
                # Create trade record
                trade = Trade(
                    price=current_price,
                    amount=coin_amount,
                    fee=fee,
                    executed_at=timezone.now(),
                    buyer=user,
                    cryptocurrency=crypto,
                    buy_order=order,
                    sell_order=None
                )
                trade.save()
                trade_id = trade.id
                
                # Update or create crypto balance locally
                crypto_balance, created = UserAsset.objects.get_or_create(
                    cryptocurrency=crypto,
                    defaults={"balance": 0}
                )
                crypto_balance.balance += coin_amount
                crypto_balance.save()
        except Exception as e:
            return {"success": False, "error": f"Local database error: {str(e)}"}
        
        return {
            "success": True,
            "order_id": order.id,
            "trade_id": trade_id,
            "external_order_id": external_order_id,
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