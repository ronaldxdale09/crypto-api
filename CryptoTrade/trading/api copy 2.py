from ninja import Router
from typing import List, Optional
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
import requests
import json
from user_account.models import User
from crypto_currency.models import Cryptocurrency
from .models import Order, Trade, TradingPair
from .forms import *

router = Router()

ORDER_API_URL = "https://wallet-app-api-main-m41zlt.laravel.cloud/api/v1/orders"
WALLET_API_URL = "https://wallet-app-api-main-m41zlt.laravel.cloud/api/v1/user-wallet"
API_KEY = "A20RqFwVktRxxRqrKBtmi6ud"



def create_external_order(order_data):
    """
    Create an order using the external API.
    
    Args:
        order_data (dict): Order data containing relevant parameters
    
    Returns:
        dict: {
            'success': bool,
            'error': str or None
        }
    """
    # Build the URL with query parameters
    url = f"{ORDER_API_URL}?apikey={API_KEY}"
    
    # Add all other parameters as query parameters
    for key, value in order_data.items():
        url += f"&{key}={value}"
    
    print(f"Making request to: {url}")  # For debugging
    
    try:
        headers = {
            "Accept": "application/json"
        }
        
        # Use GET instead of POST based on your example URL
        api_response = requests.get(
            url,
            headers=headers,
            timeout=15
        )
        
        # Check if request was successful
        if api_response.status_code not in (200, 201):
            return {
                'success': False,
                'error': f"External API request failed with status code: {api_response.status_code}. Response: {api_response.text}"
            }
        
        # If successful, simply return success
        return {
            'success': True,
            'error': None
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f"Unexpected error: {str(e)}"
        }
    


def get_user_wallet(uid, coin_id=None):
    """
    Get user wallet information from the external wallet API.
    
    Args:
        uid (str): User identifier
        coin_id (int, optional): Specific coin ID to query
        
    Returns:
        dict: {
            'success': bool,
            'wallet_data': dict or None,
            'spot_balance': Decimal or None,
            'error': str or None
        }
    """
    headers = {
        "Accept": "application/json"
    }
    
    # The API requires both uid and coin_id
    # If coin_id is not provided, use default value 1 (assuming it's for USDT)
    if not coin_id:
        coin_id = 1
    
    # Construct the URL according to the working example
    url = f"{WALLET_API_URL}/{uid}/{coin_id}?apikey={API_KEY}"
    
    try:
        print(f"Making request to: {url}")  # For debugging
        api_response = requests.get(
            url,
            headers=headers,
            timeout=10  # Set timeout to avoid hanging requests
        )
        
        # Check if request was successful
        if api_response.status_code != 200:
            return {
                'success': False,
                'wallet_data': None,
                'spot_balance': None,
                'error': f"Wallet API request failed with status code: {api_response.status_code}. URL: {url}"
            }
        
        # Parse wallet data
        wallet_data = api_response.json()
        
        # Check if wallet data exists
        if not wallet_data:
            return {
                'success': False,
                'wallet_data': None,
                'spot_balance': None,
                'error': "No wallet data found"
            }
        
        # Extract spot wallet balance based on the structure you provided
        # Assuming the JSON is a string that needs to be parsed
        if isinstance(wallet_data, str):
            try:
                wallet_data = json.loads(wallet_data)
            except json.JSONDecodeError:
                pass
        
        # Try to extract spot wallet balance
        spot_balance = None
        if isinstance(wallet_data, dict):
            if 'usdtWallet' in wallet_data:
                spot_balance = Decimal(str(wallet_data['usdtWallet']['spot_wallet']))
            elif 'cryptoWallet' in wallet_data:
                spot_balance = Decimal(str(wallet_data['cryptoWallet']['spot_wallet']))
        
        return {
            'success': True,
            'wallet_data': wallet_data,
            'spot_balance': spot_balance,
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
            "is_active": pair.is_active,
            "external_pair_id": pair.external_pair_id
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
@router.post('/order', response=OrderResponseSchema)
def create_order(request, form: CreateOrderSchema):
    """Create a buy or sell order (market or limit)."""
    try:
        user = get_object_or_404(User, uid=form.uid)
        
        # Validate order type
        if form.order_type not in ['buy', 'sell']:
            return {"success": False, "error": "Invalid order type"}
        
        # Validate order execution type (market or limit)
        if form.execution_type not in ['market', 'limit']:
            return {"success": False, "error": "Invalid execution type"}

        # Calculate total amount in USDT
        total_in_usdt = form.price * form.amount
        
        # For buy orders, check if user has enough balance
        if form.order_type == 'buy':
            wallet_result = get_user_wallet(form.uid, 2)  # Assuming 2 is USDT
            if not wallet_result['success']:
                return {"success": False, "error": wallet_result['error']}
                
            # Parse wallet data to get spot balance
            wallet_data = wallet_result['wallet_data']
            if isinstance(wallet_data, str):
                try:
                    wallet_data = json.loads(wallet_data)
                except json.JSONDecodeError:
                    return {"success": False, "error": "Invalid wallet data format"}
                    
            if 'usdtWallet' in wallet_data:
                spot_wallet_balance = Decimal(str(wallet_data['usdtWallet']['spot_wallet']))
            else:
                return {"success": False, "error": "Could not determine USDT wallet balance"}
                
            if spot_wallet_balance < total_in_usdt:
                return {"success": False, "error": "Insufficient balance in spot wallet"}
        
        # Fetch coin details from API to get coin_pair_id
        COIN_API_URL = "https://wallet-app-api-main-m41zlt.laravel.cloud/api/v1/coins"
        coin_response = requests.get(f"{COIN_API_URL}?apikey={API_KEY}")
        
        if coin_response.status_code != 200:
            return {"success": False, "error": f"Failed to fetch coin details: {coin_response.status_code}"}
            
        coins = coin_response.json()
        
        # Find the matching coin by ID or symbol
        crypto_id = form.crypto_id
        
        # Prepare data for external API call
        order_data = {
            'uid': form.uid,
            'coin_pair_id': crypto_id,  # Use the provided crypto ID as the pair ID
            'wallet_id': form.wallet_id,
            'order_type': form.order_type,
            'excecution_type': form.execution_type,
            'price': float(form.price),
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
                cryptocurrency_id=crypto_id,  # Store the ID directly
                order_type=form.order_type,
                execution_type=form.execution_type,
                price=form.price,
                amount=form.amount,
                total_in_usdt=total_in_usdt,
                status='pending',
                # external_order_id=api_result['order_id']
            )
        
        return {
            "success": True,
            "order": {
                "id": order.id,
                "user_id": order.user.id,
                "cryptocurrency_id": crypto_id,
                "order_type": order.order_type,
                "execution_type": order.execution_type,
                "price": order.price,
                "amount": order.amount,
                "total_in_usdt": order.total_in_usdt,
                "trade_fee": order.trade_fee,
                "status": order.status,
                "created_at": order.created_at,
                "completed_at": order.completed_at,
                # "external_order_id": order.external_order_id
            }
        }
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

@router.post('/order/{order_id}/cancel', response=OrderResponseSchema)
def cancel_order(request, order_id: int, form: CancelOrderSchema):
    """Cancel a pending order."""
    order = get_object_or_404(Order, id=order_id)
    
    # Security check - ensure the user owns this order
    if order.user.uid != form.uid:
        return {"success": False, "error": "Unauthorized"}
    
    # Check if the order can be cancelled
    if order.status != 'pending':
        return {"success": False, "error": f"Cannot cancel order in {order.status} state"}
    
    with transaction.atomic():
        order.status = 'cancelled'
        order.save()
        
    return {
        "success": True,
        "order": {
            "id": order.id,
            "user_id": order.user.id,
            "cryptocurrency_id": order.cryptocurrency.id,
            "order_type": order.order_type,
            "execution_type": order.execution_type,
            "price": order.price,
            "amount": order.amount,
            "total_in_usdt": order.total_in_usdt,
            "trade_fee": order.trade_fee,
            "status": order.status,
            "created_at": order.created_at,
            "completed_at": order.completed_at
            # "external_order_id": order.external_order_id
        }
    }


@router.get('/order/user={uid}', response=OrderListResponseSchema, tags=["Trading"])
def get_user_orders(request, uid: str):
    """Get all orders for a user."""
    # Get user instance
    user = get_object_or_404(User, uid=uid)

    # Get all orders for the user
    orders = Order.objects.filter(user=user).order_by('-created_at')

    # Serialize orders
    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "user_id": order.user.id,
            "cryptocurrency_id": order.cryptocurrency.id,
            "order_type": order.order_type,
            "execution_type": order.execution_type,
            "price": order.price,
            "amount": order.amount,
            "total_in_usdt": order.total_in_usdt,
            "trade_fee": order.trade_fee,
            "status": order.status,
            "created_at": order.created_at,
            "completed_at": order.completed_at if order.completed_at else None,
            "external_order_id": order.external_order_id
        })

    return {
        "orders": result,
        "count": len(result)
    }

@router.get('/trades/{uid}', response=TradeListResponseSchema, tags=["Trading"])
def get_user_trades(request, uid: str):
    """Get trade history for a user."""
    user = get_object_or_404(User, uid=uid)
    
    # Get all trades where the user is the buyer or seller (through buy_order or sell_order)
    trades = Trade.objects.filter(
        Q(buyer=user) | Q(buy_order__user=user) | Q(sell_order__user=user)
    ).order_by('-executed_at')
    
    result = []
    for trade in trades:
        result.append({
            "id": trade.id,
            "buyer_id": trade.buyer.id if trade.buyer else None,
            "cryptocurrency_id": trade.cryptocurrency.id,
            "price": trade.price,
            "amount": trade.amount,
            "fee": trade.fee,
            "executed_at": trade.executed_at
        })
    
    return {
        "trades": result,
        "count": len(result)
    }


@router.post('/trading/buy/{uid}/{crypto_id}', response=BuySellResponseSchema, tags=["Trading"])
def buy_crypto(request, uid: str, crypto_id: int, data: BuySellSchema):
    try:
        # Get parameters from request body
        current_price = data.currentPrice
        
        # Get amount (in crypto units) or calculate from totalAmount if provided
        coin_amount = None
        total_amount = None
        
        if hasattr(data, 'amount') and data.amount is not None:
            coin_amount = data.amount
            total_amount = coin_amount * current_price
        elif hasattr(data, 'totalAmount') and data.totalAmount is not None:
            total_amount = data.totalAmount
            coin_amount = total_amount / current_price
        else:
            # Default values if neither is provided
            coin_amount = Decimal('100')
            total_amount = coin_amount * current_price
        
        # Get wallet_id if provided
        wallet_id = None
        if hasattr(data, 'wallet_id'):
            wallet_id = data.wallet_id
        
        # Validate values are positive
        if current_price <= 0:
            return {"success": False, "error": "Price must be greater than zero"}
        if coin_amount <= 0:
            return {"success": False, "error": "Amount must be greater than zero"}
        
        # Get user
        user = get_object_or_404(User, uid=uid)
        
        # Get user wallet data if wallet_id not provided
        if wallet_id is None:
            wallet_result = get_user_wallet(uid, 2)  # Assuming 2 is USDT
            if not wallet_result['success']:
                return {"success": False, "error": wallet_result['error']}
                
            wallet_data = wallet_result['wallet_data']
            
            # Parse the wallet data if it's a string
            if isinstance(wallet_data, str):
                try:
                    wallet_data = json.loads(wallet_data)
                except json.JSONDecodeError:
                    return {"success": False, "error": "Invalid wallet data format"}
            
            # Try to get the wallet_id
            if 'usdtWallet' in wallet_data and 'wallet_id' in wallet_data['usdtWallet']:
                wallet_id = wallet_data['usdtWallet']['wallet_id']
            
        # If still no wallet_id, use the one from your example URL
        if wallet_id is None:
            wallet_id = 46
            
        # Calculate fee
        fee = total_amount * Decimal('0.001')  # 0.1% fee
            
        # Prepare data for external order API
        order_data = {
            'uid': uid,
            'coin_pair_id': crypto_id,
            'wallet_id': wallet_id,
            'order_type': 'buy',
            'excecution_type': 'market',
            'price': float(current_price),
            'amount': float(coin_amount),
            'total_in_usdt': float(total_amount)
        }
        
        # Call external API to create order
        api_result = create_external_order(order_data)
        if not api_result['success']:
            return {"success": False, "error": api_result['error']}
        
        try:
            with transaction.atomic():
                # Create local order record
                order = Order(
                    user=user,
                    cryptocurrency_id=crypto_id,
                    order_type='buy',
                    execution_type='market',
                    price=current_price,
                    amount=coin_amount,
                    total_in_usdt=total_amount,
                    trade_fee=fee,
                    status='completed',
                    completed_at=timezone.now()
                )
                order.save()
                
                # Create trade record
                trade = Trade(
                    buyer=user,
                    cryptocurrency_id=crypto_id,
                    buy_order=order,
                    price=current_price,
                    amount=coin_amount,
                    fee=fee,
                    executed_at=timezone.now()
                )
                trade.save()
        except Exception as e:
            return {"success": False, "error": f"Database error: {str(e)}"}
        
        return {
            "success": True,
            "order_id": order.id,
            "trade_id": trade.id,
            "price": current_price,
            "amount": coin_amount,
            "total_amount": total_amount,
            "fee": fee
        }
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}
    

@router.post('/trading/sell/{uid}/{crypto_id}', response=BuySellResponseSchema, tags=["Trading"])
def sell_crypto(request, uid: str, crypto_id: int, data: BuySellSchema):
    """
    Sell cryptocurrency at market price.
    
    Path parameters:
    - uid: Unique identifier of the user selling
    - crypto_id: ID of the cryptocurrency to sell
    
    Body parameters:
    - wallet_id: (Optional) ID of the wallet to use
    - currentPrice: Current price of the cryptocurrency
    - amount: Amount in coins to sellx  
    """
    try:
        # Get parameters from request body
        current_price = data.currentPrice
        coin_amount = data.amount
        
        # Handle optional wallet_id
        wallet_id = None
        # Check if wallet_id attribute exists and use it if available
        try:
            wallet_id = getattr(data, 'wallet_id', None)
        except:
            pass
        
        # Validate values are positive
        if current_price <= 0:
            return {"success": False, "error": "Price must be greater than zero"}
        if coin_amount <= 0:
            return {"success": False, "error": "Amount must be greater than zero"}
        
        # Get user
        user = get_object_or_404(User, uid=uid)
        
        # Calculate total value
        total_value = coin_amount * current_price
        fee = total_value * Decimal('0.001')  # 0.1% fee
        
        # Get crypto wallet data to check balance
        crypto_wallet_result = get_user_wallet(uid, crypto_id)
        if not crypto_wallet_result['success']:
            return {"success": False, "error": crypto_wallet_result['error']}
            
        crypto_wallet_data = crypto_wallet_result['wallet_data']
        
        # If crypto_wallet_data is a string, try to parse it
        if isinstance(crypto_wallet_data, str):
            try:
                crypto_wallet_data = json.loads(crypto_wallet_data)
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid wallet data format"}
        
        # Check if crypto wallet exists and has sufficient balance
        if not crypto_wallet_data or 'cryptoWallet' not in crypto_wallet_data:
            return {"success": False, "error": "Crypto wallet not found"}
        
        # If wallet_id wasn't provided, try to get it from the wallet data
        if wallet_id is None and 'cryptoWallet' in crypto_wallet_data and 'wallet_id' in crypto_wallet_data['cryptoWallet']:
            wallet_id = crypto_wallet_data['cryptoWallet']['wallet_id']
        
        # If still no wallet_id, return error
        if wallet_id is None:
            return {"success": False, "error": "Could not determine wallet ID"}
            
        crypto_balance = Decimal(str(crypto_wallet_data['cryptoWallet']['spot_wallet']))
        if crypto_balance < coin_amount:
            return {"success": False, "error": "Insufficient cryptocurrency balance"}
        
        # Use the crypto_id directly for the coin_pair_id
        # Instead of trying to find a trading pair
            
        # Prepare data for external order API
        order_data = {
            'uid': uid,
            'coin_pair_id': crypto_id,
            'wallet_id': wallet_id,
            'order_type': 'sell',
            'excecution_type': 'market',
            'price': float(current_price),
            'amount': float(coin_amount),
            'total_in_usdt': float(total_value)
        }
        
        # Call external API to create sell order
        api_result = create_external_order(order_data)
        if not api_result['success']:
            return {"success": False, "error": api_result['error']}
            
        external_order_id = api_result['order_id']
        
        try:
            with transaction.atomic():
                # Create local order record
                order = Order(
                    user=user,
                    cryptocurrency_id=crypto_id,  # Use cryptocurrency_id directly
                    order_type='sell',
                    execution_type='market',
                    price=current_price,
                    amount=coin_amount,
                    total_in_usdt=total_value,
                    trade_fee=fee,
                    status='completed',
                    completed_at=timezone.now(),
                    external_order_id=external_order_id
                )
                order.save()
                
                # Create trade record
                trade = Trade(
                    cryptocurrency_id=crypto_id,  # Use cryptocurrency_id directly
                    sell_order=order,
                    price=current_price,
                    amount=coin_amount,
                    fee=fee,
                    executed_at=timezone.now()
                )
                trade.save()
        except Exception as e:
            return {"success": False, "error": f"Database error: {str(e)}"}
        
        return {
            "success": True,
            "order_id": order.id,
            "trade_id": trade.id,
            "external_order_id": external_order_id,
            "price": current_price,
            "amount": coin_amount,
            "total_amount": total_value,
            "fee": fee
        }
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}