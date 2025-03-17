from ninja import Router
from typing import List, Optional
from decimal import Decimal
from django.shortcuts import get_object_or_404
import requests
import json
import time
from user_account.models import User
from .forms import BuySellSchema, BuySellResponseSchema

router = Router()

ORDER_API_URL = "https://wallet-app-api-main-m41zlt.laravel.cloud/api/v1/orders"
WALLET_API_URL = "https://wallet-app-api-main-m41zlt.laravel.cloud/api/v1/user-wallet"
API_KEY = "A20RqFwVktRxxRqrKBtmi6ud"

def create_external_order(uid, coin_pair_id, wallet_id, order_type, excecution_type, price, amount, total_in_usdt):
    """
    Create an order using the external API with URL parameters.
    
    Args:
        uid (str): User ID
        coin_pair_id (int): Coin pair ID
        wallet_id (int): Wallet ID
        order_type (str): Order type (buy/sell)
        excecution_type (str): Execution type (market/limit)
        price (float): Price
        amount (float): Amount
        total_in_usdt (float): Total in USDT
    
    Returns:
        dict: Response with success status and order details
    """
    try:
        headers = {
            "Accept": "application/json"
        }
        
        # Build URL with query parameters exactly as shown in the example
        url = f"{ORDER_API_URL}?apikey={API_KEY}&uid={uid}&coin_pair_id={coin_pair_id}&wallet_id={wallet_id}&order_type={order_type}&excecution_type={excecution_type}&price={price}&amount={amount}&total_in_usdt={total_in_usdt}"
        
        print(f"Making request to: {url}")
        
        # Use GET request as shown in the example URL
        api_response = requests.get(
            url,
            headers=headers,
            timeout=15
        )
        
        print(f"Response status: {api_response.status_code}")
        print(f"Response body: {api_response.text}")
        
        # Check if request was successful
        if api_response.status_code not in (200, 201):
            return {
                'success': False,
                'order_data': None,
                'order_id': None,
                'error': f"Order API: External API request failed with status code: {api_response.status_code}. Response: {api_response.text}",
                'raw_response': None
            }
        
        # Parse response data
        try:
            response_data = api_response.json()
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'order_data': None,
                'order_id': None,
                'error': f"Failed to parse JSON response: {str(e)}",
                'raw_response': api_response.text
            }
        
        if not response_data:
            return {
                'success': False,
                'order_data': None,
                'order_id': None,
                'error': "Empty response from API",
                'raw_response': response_data
            }
            
        # Check various possible response structures
        if 'id' in response_data:
            return {
                'success': True,
                'order_data': response_data,
                'order_id': response_data['id'],
                'error': None,
                'raw_response': response_data
            }
        elif 'data' in response_data and isinstance(response_data['data'], list) and len(response_data['data']) > 0:
            latest_order = response_data['data'][-1]
            return {
                'success': True,
                'order_data': latest_order,
                'order_id': latest_order.get('id'),
                'error': None,
                'raw_response': response_data
            }
        elif 'data' in response_data and isinstance(response_data['data'], dict):
            return {
                'success': True,
                'order_data': response_data['data'],
                'order_id': response_data['data'].get('id'),
                'error': None,
                'raw_response': response_data
            }
        
        return {
            'success': True,  # Even without specific order data, if API returned 200, consider it successful
            'order_data': response_data,
            'order_id': None,
            'error': None,
            'raw_response': response_data
        }
        
    except Exception as e:
        print(f"Error in create_external_order: {str(e)}")
        return {
            'success': False,
            'order_data': None,
            'order_id': None,
            'error': f"Error: {str(e)}",
            'raw_response': None
        }

def get_user_wallet(uid, coin_id=None):
    """
    Get user wallet information from the external wallet API.
    
    Args:
        uid (str): User identifier
        coin_id (int, optional): Specific coin ID to query
    """
    headers = {
        "Accept": "application/json"
    }
    
    # Default to USDT (coin_id=2) if not specified
    if not coin_id:
        coin_id = 2
    
    # Construct proper URL for wallet API
    url = f"{WALLET_API_URL}/{uid}/{coin_id}?apikey={API_KEY}"
    
    try:
        print(f"Making request to: {url}")
        api_response = requests.get(
            url,
            headers=headers,
            timeout=10
        )
        
        if api_response.status_code != 200:
            return {
                'success': False,
                'wallet_data': None,
                'spot_balance': None,
                'wallet_id': None,
                'error': f"Wallet API request failed with status code: {api_response.status_code}. URL: {url}"
            }
        
        try:
            wallet_data = api_response.json()
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'wallet_data': None,
                'spot_balance': None,
                'wallet_id': None,
                'error': f"Failed to parse wallet JSON: {str(e)}"
            }
        
        if not wallet_data:
            return {
                'success': False,
                'wallet_data': None,
                'spot_balance': None,
                'wallet_id': None,
                'error': "No wallet data found"
            }
        
        # Extract spot wallet balance based on the actual structure shown in your screenshot
        spot_balance = None
        wallet_id = None
        
        if isinstance(wallet_data, dict):
            # First check for cryptoWallet
            if 'cryptoWallet' in wallet_data and wallet_data['cryptoWallet'] is not None:
                crypto_wallet = wallet_data['cryptoWallet']
                spot_balance = Decimal(str(crypto_wallet.get('spot_wallet', '0')))
                wallet_id = crypto_wallet.get('wallet_id')
            
            # Then check for usdtWallet (if we're querying USDT)
            elif 'usdtWallet' in wallet_data and wallet_data['usdtWallet'] is not None:
                usdt_wallet = wallet_data['usdtWallet']
                spot_balance = Decimal(str(usdt_wallet.get('spot_wallet', '0')))
                wallet_id = usdt_wallet.get('wallet_id')
        
        return {
            'success': True,
            'wallet_data': wallet_data,
            'spot_balance': spot_balance,
            'wallet_id': wallet_id,
            'error': None
        }
    
    except Exception as e:
        return {
            'success': False,
            'wallet_data': None,
            'spot_balance': None,
            'wallet_id': None,
            'error': f"Error: {str(e)}"
        }

@router.post('/trading/buy/{uid}/{coin_pair_id}', response=BuySellResponseSchema, tags=["Trading"])
def buy_crypto(request, uid: str, coin_pair_id: int, data: BuySellSchema):
    """
    Buy cryptocurrency directly at market price.
    
    Path parameters:
    - uid: Unique identifier of the user making the purchase
    - coin_pair_id: ID of the cryptocurrency pair to buy
    
    Body parameters:
    - currentPrice: Current price of the cryptocurrency
    - amount: Amount of cryptocurrency to buy
    - wallet_id: Wallet ID to use
    - execution_type: Type of execution (market or limit)
    """
    try:
        # Extract parameters from request
        current_price = data.currentPrice
        coin_amount = data.amount
        
        # Get required parameters
        wallet_id = getattr(data, 'wallet_id', None)
        execution_type = getattr(data, 'execution_type', 'market')
        
        # Validate wallet_id is provided
        if wallet_id is None:
            # Try to get from wallet
            wallet_result = get_user_wallet(uid, 2)  # 2 = USDT
            if wallet_result['success'] and wallet_result['wallet_id'] is not None:
                wallet_id = wallet_result['wallet_id']
            else:
                return {"success": False, "error": "wallet_id is required"}
        
        # Calculate total value
        total_value = coin_amount * current_price
        
        # Validate inputs
        if current_price <= 0 or coin_amount <= 0:
            return {"success": False, "error": "Price and amount must be greater than zero"}
        
        # Calculate fee (if needed)
        fee = total_value * Decimal('0.001')  # 0.1% fee
        
        # Call external API to create order with all parameters
        api_result = create_external_order(
            uid=uid,
            coin_pair_id=coin_pair_id,
            wallet_id=wallet_id,
            order_type='buy',
            excecution_type=execution_type,
            price=float(current_price),
            amount=float(coin_amount),
            total_in_usdt=float(total_value)
        )
        
        if not api_result['success']:
            return {"success": False, "error": api_result['error']}
        
        # Allow a brief delay for balance updates
        time.sleep(2)
            
        # Get the final wallet balances after the transaction
        final_usdt_wallet = get_user_wallet(uid, 2)
        final_crypto_wallet = get_user_wallet(uid, coin_pair_id)
        
        # Prepare comprehensive response
        return {
            "success": True,
            "external_order_id": api_result.get('order_id'),
            "transaction_details": {
                "price": current_price,
                "amount": coin_amount,
                "total_value": total_value,
                "fee": fee
            },
            "wallet_details": {
                "wallet_id": wallet_id,
                "usdt_balance": final_usdt_wallet['spot_balance'] if final_usdt_wallet['success'] else None,
                "crypto_balance": final_crypto_wallet['spot_balance'] if final_crypto_wallet['success'] else None
            },
            "external_api_response": api_result.get('raw_response')
        }
        
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}\nTrace: {trace}"}

@router.post('/trading/sell/{uid}/{coin_pair_id}', response=BuySellResponseSchema, tags=["Trading"])
def sell_crypto(request, uid: str, coin_pair_id: int, data: BuySellSchema):
    """
    Sell cryptocurrency at market price.
    
    Path parameters:
    - uid: Unique identifier of the user selling
    - coin_pair_id: ID of the cryptocurrency pair to sell
    
    Body parameters:
    - currentPrice: Current price of the cryptocurrency
    - amount: Amount in coins to sell
    - wallet_id: Wallet ID to use
    - execution_type: Type of execution (market or limit)
    """
    try:
        # Extract parameters from request
        current_price = data.currentPrice
        coin_amount = data.amount
        
        # Get required parameters
        wallet_id = getattr(data, 'wallet_id', None)
        execution_type = getattr(data, 'execution_type', 'market')
        
        # Validate wallet_id is provided
        if wallet_id is None:
            # Try to get from wallet
            wallet_result = get_user_wallet(uid, coin_pair_id)
            if wallet_result['success'] and wallet_result['wallet_id'] is not None:
                wallet_id = wallet_result['wallet_id']
            else:
                return {"success": False, "error": "wallet_id is required"}
        
        # Calculate total value
        total_value = coin_amount * current_price
        
        # Validate inputs
        if current_price <= 0 or coin_amount <= 0:
            return {"success": False, "error": "Price and amount must be greater than zero"}
        
        # Calculate fee
        fee = total_value * Decimal('0.001')  # 0.1% fee
        
        # Call external API to create order with all parameters
        api_result = create_external_order(
            uid=uid,
            coin_pair_id=coin_pair_id,
            wallet_id=wallet_id,
            order_type='sell',
            excecution_type=execution_type,
            price=float(current_price),
            amount=float(coin_amount),
            total_in_usdt=float(total_value)
        )
        
        if not api_result['success']:
            return {"success": False, "error": api_result['error']}
        
        # Allow a brief delay for balance updates
        time.sleep(2)
        
        # Get the final wallet balances after the transaction
        final_usdt_wallet = get_user_wallet(uid, 2)
        final_crypto_wallet = get_user_wallet(uid, coin_pair_id)
        
        # Prepare comprehensive response
        return {
            "success": True,
            "external_order_id": api_result.get('order_id'),
            "transaction_details": {
                "price": current_price,
                "amount": coin_amount,
                "total_value": total_value,
                "fee": fee
            },
            "wallet_details": {
                "wallet_id": wallet_id,
                "usdt_balance": final_usdt_wallet['spot_balance'] if final_usdt_wallet['success'] else None,
                "crypto_balance": final_crypto_wallet['spot_balance'] if final_crypto_wallet['success'] else None
            },
            "external_api_response": api_result.get('raw_response')
        }
        
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}\nTrace: {trace}"}