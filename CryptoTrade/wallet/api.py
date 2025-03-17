from ninja import Router
from crypto_currency.models import *
from user_account.models import *
from .models import *
from .forms import *
from ninja import Schema
from typing import List, Optional
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
import uuid
import requests

router = Router()

CRYPTO_LOGO_PATHS = {
    "BTC": "https://shorturl.at/jbnPp",
    "DOGE": "https://iimbltovdjhoifnmzims.supabase.co/storage/v1/object/sign/crypto_app/crypto/Dogecoin.png?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJjcnlwdG9fYXBwL2NyeXB0by9Eb2dlY29pbi5wbmciLCJpYXQiOjE3NDExMDA0NzgsImV4cCI6MTc0OTY1NDA3OH0.uupInNHoBmUoa-s-EhNcnthZBz_1nbwIum1goCd0KW8",
    "ETH": "https://iimbltovdjhoifnmzims.supabase.co/storage/v1/object/sign/crypto_app/crypto/ethereum.png?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJjcnlwdG9fYXBwL2NyeXB0by9ldGhlcmV1bS5wbmciLCJpYXQiOjE3NDExMDA1MDMsImV4cCI6MTc0OTY1NDEwM30.prgNNelliJr75t8RTFC1u--DSWDJBCS0A9HSTiZz2Ew",
    "SOL": "https://iimbltovdjhoifnmzims.supabase.co/storage/v1/object/sign/crypto_app/crypto/Solana.png?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJjcnlwdG9fYXBwL2NyeXB0by9Tb2xhbmEucG5nIiwiaWF0IjoxNzQxMTAwNTI3LCJleHAiOjE3NDk2NTQxMjd9.VbbJ14SUdI6sw0st83Bli9YNHOH4Da-LRln5e2vulWs",
    "XRP": "https://iimbltovdjhoifnmzims.supabase.co/storage/v1/object/sign/crypto_app/crypto/XRP.png?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJjcnlwdG9fYXBwL2NyeXB0by9YUlAucG5nIiwiaWF0IjoxNzQxMTAwNTUwLCJleHAiOjE3NDk2NTQxNTB9.LMoEs_Wqvj5KbprILXSJQSLmRGZUYtqHB7ZOv2xRQoQ"
}
# Schema definitions for request and response
class UserAssetSchema(Schema):
    wallet_id: int
    crypto_id: int
    balance: Decimal

class WalletInfoSchema(Schema):
    id: int
    available_balance: Decimal
    wallet_address: Optional[str]
    is_active: bool

class TransactionSchema(Schema):
    id: int
    type: str
    amount: Decimal
    fee: Decimal
    status: str
    timestamp: str = None

# class WithdrawRequestSchema(Schema):
#     wallet_id: int
#     crypto_id: int
#     amount: Decimal
#     address: str
#     network_id: int

class DepositAddressSchema(Schema):
    wallet_id: int
    crypto_id: int
    network_id: int

class TransferRequestSchema(Schema):
    from_wallet_id: int
    to_wallet_id: int
    crypto_id: int
    amount: Decimal

class SendRequestSchema(Schema):
    wallet_id: int
    crypto_id: int
    network_id: int
    amount: Decimal
    recipient_address: str
    memo: Optional[str] = None  # Optional memo/tag field for certain blockchains


# Endpoints
@router.post('/create-wallet')
def create_wallet_for_user(request, user_id: int):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User not found"}

    # Create wallet instance
    wallet = Wallet.objects.create()
    wallet.user_id.add(user)

    # Initialize UserAsset for each cryptocurrency
    cryptocurrencies = Cryptocurrency.objects.all()
    UserAsset.objects.bulk_create([
        UserAsset(wallet=wallet, cryptocurrency=crypto, balance=0.0)
        for crypto in cryptocurrencies
    ])

    return {
        "success": "Wallet successfully created for the user!",
        "user_id": user.id,
        "wallet_id": wallet.id,
        "cryptocurrencies": [crypto.symbol for crypto in cryptocurrencies]
    }

#Fetching user wallets
@router.get('/getWallets/')
def getUserWalletsNBalance(request, user_id: int):
    wallets = Wallet.objects.filter(user_id=user_id)
    if not wallets.exists():
        return {"message": "No wallets found for this user"}

    response_data = []
    for wallet in wallets:
        user_wallet_balance_instances = UserAsset.objects.filter(wallet=wallet).select_related('cryptocurrency', 'network')
        wallet_data = [
            {
                "wallet_id": wallet.id,
                "crypto_id": balance.cryptocurrency.id if balance.cryptocurrency else 0,
                "crypto_name": balance.cryptocurrency.name if balance.cryptocurrency else "Unknown",
                "crypto_symbol": balance.cryptocurrency.symbol if balance.cryptocurrency else "N/A",
                "crypto_description": balance.cryptocurrency.crypto_description if balance.cryptocurrency else "No description available",
                "network": balance.network.name if balance.network else "Unknown",
                "balance": float(balance.balance) if balance.balance != 0 else 0.0
            }
            for balance in user_wallet_balance_instances
        ]
        response_data.append({
            "wallet_id": wallet.id,
            "balances": wallet_data
        })

    return response_data


@router.get('/getUserAsset', response=List[UserAssetSchema])
def get_user_asset(request):
    """Get all user_asset."""
    balances = UserAsset.objects.all()
    return [
        {
            "wallet_id": balance.wallet.id,
            "crypto_id": balance.cryptocurrency.id,
            "balance": balance.balance
        } for balance in balances
    ]

@router.get('/wallet/{wallet_id}', response=WalletInfoSchema)
def get_wallet(request, wallet_id: int):
    """Get wallet information by ID."""
    wallet = get_object_or_404(Wallet, id=wallet_id)
    return {
        "id": wallet.id,
        "available_balance": wallet.available_balance,
        "wallet_address": wallet.wallet_address,
        "is_active": wallet.is_active
    }
#get selecting the default wallet
@router.get('/user_asset/')
def getUserAsset(request, user_id: int):
    wallet_instance = Wallet.objects.get(user_id=user_id)
    
    # Get all user assets tied to the wallet
    user_assets = UserAsset.objects.select_related('cryptocurrency').filter(wallet=wallet_instance)
    
    # Build the response data
    data = []
    for asset in user_assets:
        crypto = asset.cryptocurrency
        logo_url = CRYPTO_LOGO_PATHS.get(crypto.symbol, "")
        
        data.append({
            "wallet_id": wallet_instance.id,
            "cryptocurrency": {
                "id": crypto.id,
                "symbol": crypto.symbol,
                "name": crypto.name,
                "price": str(crypto.price),
                "logo_url": logo_url
            },
            "balance": str(asset.balance or Decimal('0.0')),
            "updated_at": asset.updated_at,
        })
        
    return JsonResponse({"status": "success", "data": data})

#can select wallet
@router.get('/user_asset/{user_id}/{wallet_id}')
def getUserWalletAsset(request, user_id: int, wallet_id:int):
        wallet_instance = Wallet.objects.get(user_id=user_id, id=wallet_id)
        
        user_assets = UserAsset.objects.select_related('cryptocurrency').filter(wallet=wallet_instance)
        
        data = []
        for asset in user_assets:
            crypto = asset.cryptocurrency
            logo_url = CRYPTO_LOGO_PATHS.get(crypto.symbol, "")

            data.append({
                "wallet_id": wallet_instance.id,
                "cryptocurrency": {
                    "id": crypto.id,
                    "symbol": crypto.symbol,
                    "name": crypto.name,
                    "price": str(crypto.price),
                    "logo_url": logo_url
                },
                "balance": str(asset.balance or Decimal('0.0')),
                "updated_at": asset.updated_at.isoformat(),
            })
        
        return JsonResponse({"status": "success", "data": data})



# @router.get('/wallet/{wallet_id}/balances', response=List[UserAssetSchema])
# def get_wallet_balances(request, wallet_id: int):
#     """Get all cryptocurrency balances for a specific wallet."""
#     wallet = get_object_or_404(Wallet, id=wallet_id)
#     balances = UserAsset.objects.filter(wallet=wallet)
#     return [
#         {
#             "wallet_id": balance.wallet.id,
#             "crypto_id": balance.cryptocurrency.id,
#             "balance": balance.balance
#         } for balance in balances
#     ]

@router.get('/wallet/{wallet_id}/transactions', response=List[TransactionSchema])
def get_wallet_transactions(request, wallet_id: int):
    """Get all transactions for a specific wallet."""
    wallet = get_object_or_404(Wallet, id=wallet_id)
    transactions = Transaction.objects.filter(wallet_id=wallet)
    return [
        {
            "id": tx.id,
            "type": tx.type,
            "amount": tx.amount,
            "fee": tx.fee,
            "status": tx.status,
            "timestamp": tx.timestamp if hasattr(tx, 'timestamp') else None
        } for tx in transactions
    ]

@router.post('/withdraw')
def withdraw(request ,form: WithdrawRequestSchema):
    """Withdraw cryptocurrency from wallet (OKX-style)."""
    wallet = get_object_or_404(Wallet, id=form.wallet_id)
    crypto = get_object_or_404(Cryptocurrency, id=form.crypto_id)
    network = get_object_or_404(Network, id=form.network_id)

    # Validate wallet balance
    try:
        wallet_balance = UserAsset.objects.get(wallet=wallet, cryptocurrency=crypto, network=network)
    except UserAsset.DoesNotExist:
        return {"error": "No balance found for this cryptocurrency and network."}

    if wallet_balance.balance < form.amount:
        return {"error": "Insufficient balance."}

    # Calculate withdrawal fee (example: 0.1% of transaction amount)
    fee = form.amount * Decimal('0.001')
    total_amount = form.amount + fee

    # Create a pending transaction
    transaction = Transaction.objects.create(
        type="withdraw",
        amount=form.amount,
        fee=fee,
        status="pending",
        tx_hash=None,
        destination_address=form.destination_address,
        cryptocurrency=crypto,
        network=network,
        # memo=form.memo,
        comment=form.comment,
        estimated_completion_time=timezone.now() + timezone.timedelta(minutes=30)  # Example completion estimate
    )
    transaction.wallet_id.add(wallet)

    # Update wallet balance (provisional deduction)
    wallet_balance.balance -= total_amount
    wallet_balance.last_transaction = transaction
    wallet_balance.save()

    return {
        "success": True,
        "transaction_id": transaction.id,
        "amount": form.amount,
        "fee": fee,
        "destination_address": form.destination_address,
        "status": "pending",
        "estimated_completion_time": transaction.estimated_completion_time,
    }

#Create depost address
@router.post('/deposit/address')
def get_deposit_address(request, form: DepositAddressSchema):
    """Get or create deposit address for a cryptocurrency and network."""
    wallet = get_object_or_404(Wallet, id=form.wallet_id)
    crypto = get_object_or_404(Cryptocurrency, id=form.crypto_id)
    network = get_object_or_404(Network, id=form.network_id)
    
    # Check if wallet address already exists for this network
    wallet_address = WalletAddress.objects.filter(network_id=network).first()
    
    if not wallet_address:
        # In a real application, you would integrate with blockchain APIs 
        # to generate a real address. For now, we'll simulate it
        address = f"{crypto.symbol.lower()}_{uuid.uuid4().hex[:16]}"
        wallet_address = WalletAddress.objects.create(
            address=address
        )
        wallet_address.network_id.add(network)
    
    return {
        "success": True,
        "wallet_id": form.wallet_id,
        "crypto": crypto.symbol,
        "network": network.name,
        "address": wallet_address.address
    }

@router.post('/transfer')
def transfer_crypto(request, form: TransferRequestSchema):
    """Transfer cryptocurrency between wallets."""
    from_wallet = get_object_or_404(Wallet, id=form.from_wallet_id)
    to_wallet = get_object_or_404(Wallet, id=form.to_wallet_id)
    crypto = get_object_or_404(Cryptocurrency, id=form.crypto_id)
    
    # Check if source wallet has enough balance
    try:
        from_balance = UserAsset.objects.get(wallet=from_wallet, cryptocurrency=crypto)
    except UserAsset.DoesNotExist:
        return {"error": "No balance found for this cryptocurrency in source wallet"}
    
    if from_balance.balance < form.amount:
        return {"error": "Insufficient balance"}
    
    # Get or create destination wallet balance
    to_balance, created = UserAsset.objects.get_or_create(
        wallet=to_wallet, 
        cryptocurrency=crypto,
        defaults={"balance": 0}
    )
    
    # Create transaction record
    transaction = Transaction.objects.create(
        type="transfer",
        amount=form.amount,
        fee=Decimal('0'),
        status="completed"
    )
    transaction.wallet_id.add(from_wallet)
    transaction.wallet_id.add(to_wallet)
    
    # Update balances
    from_balance.balance -= form.amount
    to_balance.balance += form.amount
    
    from_balance.save()
    to_balance.save()
    
    return {
        "success": True,
        "transaction_id": transaction.id,
        "amount": form.amount,
        "from_wallet": form.from_wallet_id,
        "to_wallet": form.to_wallet_id,
        "status": "completed"
    }

@router.get('/user/{user_id}/wallets', response=List[WalletInfoSchema])
def get_user_wallets(request, user_id: int):
    """Get all wallets for a specific user."""
    user = get_object_or_404(User, id=user_id)
    wallets = Wallet.objects.filter(user_id=user)
    
    return [
        {
            "id": wallet.id,
            "available_balance": wallet.available_balance,
            "wallet_address": wallet.wallet_address,
            "is_active": wallet.is_active
        } for wallet in wallets
    ]

@router.post('/wallet/{wallet_id}/toggle-active')
def toggle_wallet_active(request, wallet_id: int):
    """Enable or disable a wallet."""
    wallet = get_object_or_404(Wallet, id=wallet_id)
    wallet.is_active = not wallet.is_active
    wallet.save()
    
    return {
        "success": True,
        "wallet_id": wallet.id,
        "is_active": wallet.is_active,
        "status": "enabled" if wallet.is_active else "disabled"
    }

@router.get('/crypto/{crypto_id}/price')
def get_crypto_price(request, crypto_id: int):
    """
    Get current price for a cryptocurrency.
    In a real application, this would call an external API or service.
    This is a mock implementation.
    """
    crypto = get_object_or_404(Cryptocurrency, id=crypto_id)
    
    # Mock prices - in a real app, you would integrate with a price feed API
    mock_prices = {
        "BTC": 42000.50,
        "ETH": 2200.75,
        "USDT": 1.00,
        "BNB": 350.25,
        "XRP": 0.50,
    }
    
    price = mock_prices.get(crypto.symbol, 100.00)  # Default price for other cryptos
    
    return {
        "crypto_id": crypto.id,
        "symbol": crypto.symbol,
        "price_usd": price,
        "updated_at": "2025-03-03T12:00:00Z"  # Mock timestamp
    }

@router.get('/market/prices', response=List)
def get_market_prices(request):
    """
    Get current prices for all cryptocurrencies.
    In a real application, this would call an external API or service.
    """
    cryptos = Cryptocurrency.objects.all()
    
    # Mock prices - in a real app, you would integrate with a price feed API
    mock_prices = {
        "BTC": {"price": 42000.50, "change_24h": 2.5},
        "ETH": {"price": 2200.75, "change_24h": -1.2},
        "USDT": {"price": 1.00, "change_24h": 0.01},
        "BNB": {"price": 350.25, "change_24h": 3.7},
        "XRP": {"price": 0.50, "change_24h": -0.8},
    }
    
    results = []
    for crypto in cryptos:
        price_data = mock_prices.get(crypto.symbol, {"price": 100.00, "change_24h": 0.0})
        results.append({
            "crypto_id": crypto.id,
            "symbol": crypto.symbol,
            # Remove or modify this line if your Cryptocurrency model doesn't have a 'name' field
            # "name": crypto.name,
            "price_usd": price_data["price"],
            "change_24h": price_data["change_24h"],
            "updated_at": "2025-03-03T12:00:00Z"  # Mock timestamp
        })
    
    return results



# Add this new Schema to your existing Schema definitions
class SendRequestSchema(Schema):
    wallet_id: int
    crypto_id: int
    network_id: int
    amount: Decimal
    recipient_address: str
    memo: Optional[str] = None  # Optional memo/tag field for certain blockchains

# Add this new endpoint to your router
@router.post('/send')
def send_crypto(request, form: SendRequestSchema):
    """Send cryptocurrency to an external wallet address."""
    wallet = get_object_or_404(Wallet, id=form.wallet_id)
    crypto = get_object_or_404(Cryptocurrency, id=form.crypto_id)
    network = get_object_or_404(Network, id=form.network_id)
    
    # Check if wallet has enough balance
    try:
        wallet_balance = UserAsset.objects.get(
            wallet=wallet, 
            cryptocurrency=crypto,
            network=network
        )
    except UserAsset.DoesNotExist:
        return {"error": "No balance found for this cryptocurrency on the selected network"}
    
    if wallet_balance.balance < form.amount:
        return {"error": "Insufficient balance"}
    
    # Validate recipient address format (in a real app, this would be more sophisticated)
    if not form.recipient_address or len(form.recipient_address) < 10:
        return {"error": "Invalid recipient address"}
    
    # Calculate transaction fee based on the network
    # This could be more complex in a real application with dynamic fees
    fee = form.amount * Decimal('0.001')  # Example: 0.1% fee
    
    # Ensure total amount with fee doesn't exceed balance
    if wallet_balance.balance < (form.amount + fee):
        return {"error": f"Insufficient balance to cover amount plus fee ({fee} {crypto.symbol})"}
    
    # Create transaction record
    transaction = Transaction.objects.create(
        type="withdraw",  # Using withdraw type for external sends
        amount=form.amount,
        fee=fee,
        status="pending",
        destination_address=form.recipient_address,
        cryptocurrency=crypto,
        network=network
    )
    transaction.wallet_id.add(wallet)
    
    # Generate a mock transaction hash (in a real app, this would come from blockchain)
    tx_hash = f"{crypto.symbol.lower()}_tx_{uuid.uuid4().hex}"
    transaction.tx_hash = tx_hash
    transaction.save()
    
    # Update wallet balance (deducting both amount and fee)
    wallet_balance.balance -= (form.amount + fee)
    wallet_balance.last_transaction = transaction
    wallet_balance.save()
    
    # In a real application, this would trigger an actual blockchain transaction
    # For now, we'll just return the transaction details
    
    return {
        "success": True,
        "transaction_id": transaction.id,
        "tx_hash": tx_hash,
        "amount": form.amount,
        "fee": fee,
        "recipient": form.recipient_address,
        "crypto": crypto.symbol,
        "network": network.name,
        "status": "pending",
        "estimated_completion_time": "5-30 minutes"  # Mock estimation
    }



# Add this endpoint to get transaction details by ID
@router.get('/transaction/{transaction_id}')
def get_transaction_details(request, transaction_id: int):
    """Get detailed information about a specific transaction."""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Get associated wallets
    wallets = transaction.wallet_id.all()
    wallet_ids = [w.id for w in wallets]
    
    return {
        "id": transaction.id,
        "type": transaction.type,
        "amount": transaction.amount,
        "fee": transaction.fee,
        "status": transaction.status,
        "timestamp": transaction.timestamp,
        "tx_hash": transaction.tx_hash,
        "destination_address": transaction.destination_address,
        "cryptocurrency": {
            "id": transaction.cryptocurrency.id if transaction.cryptocurrency else None,
            "symbol": transaction.cryptocurrency.symbol if transaction.cryptocurrency else None,
            "name": transaction.cryptocurrency.name if transaction.cryptocurrency else None
        },
        "network": {
            "id": transaction.network.id if transaction.network else None,
            "name": transaction.network.name if transaction.network else None
        },
        "wallet_ids": wallet_ids
    }

# Add this endpoint to get estimated network fees for a cryptocurrency
@router.get('/network/{network_id}/fees')
def get_network_fees(request, network_id: int, crypto_id: int):
    """
    Get current network fee estimates for sending a cryptocurrency.
    In a real application, this would fetch actual network fee data.
    """
    network = get_object_or_404(Network, id=network_id)
    crypto = get_object_or_404(Cryptocurrency, id=crypto_id)
    
    # Mock fee data - in a real app, this would come from network-specific APIs
    # For example, Bitcoin would use different fee rates based on confirmation time
    
    # Example fee structure (would be different for each blockchain)
    fee_options = {
        "slow": {
            "fee_rate": "0.0005",  # 0.05%
            "estimated_time": "30-60 minutes"
        },
        "standard": {
            "fee_rate": "0.001",  # 0.1%
            "estimated_time": "10-30 minutes"
        },
        "fast": {
            "fee_rate": "0.002",  # 0.2%
            "estimated_time": "1-10 minutes"
        }
    }
    
    return {
        "cryptocurrency": crypto.symbol,
        "network": network.name,
        "fee_options": fee_options,
        "updated_at": "2025-03-03T12:00:00Z"  # Mock timestamp
    }


#Get user coin functionality
COIN_API_URL = "https://wallet-app-api-main-m41zlt.laravel.cloud/api/v1/coins"
USER_WALLET_API_URL = "https://wallet-app-api-main-m41zlt.laravel.cloud/api/v1/user-wallets/{uid}"

# API Key (Ensure secure storage)
API_KEY = "A20RqFwVktRxxRqrKBtmi6ud"  # Store securely

@router.get("/fetch-user-crypto", tags=["Wallet Data"])
def fetch_user_crypto(request, uid: str):
    try:
        # Fetch coins data
        coin_response = requests.get(f"{COIN_API_URL}?apikey={API_KEY}")
        coins = coin_response.json() if coin_response.status_code == 200 else []

        # Fetch user wallet data
        wallet_url = USER_WALLET_API_URL.format(uid=uid)
        wallet_response = requests.get(wallet_url, params={"apikey": API_KEY})
        wallets = wallet_response.json() if wallet_response.status_code == 200 else []

        # Create a dictionary for quick lookup of wallet balances by crypto symbol
        wallet_dict = {wallet["crypto_symbol"]: wallet["spot_wallet"] for wallet in wallets}

        # Match coins with user wallet spot balances
        matched_data = [
            {
                "symbol": coin["symbol"],
                "name": coin["name"],
                "price": coin["price"],
                "spot_wallet_balance": wallet_dict.get(coin["symbol"], "0.00000")  # Default to 0 if not found
            }
            for coin in coins
        ]

        return {"user_crypto_balances": matched_data}

    except requests.RequestException as e:
        return {"error": str(e)}