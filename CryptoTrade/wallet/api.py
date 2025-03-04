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

router = Router()

# Schema definitions for request and response
class WalletBalanceSchema(Schema):
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

class WithdrawRequestSchema(Schema):
    wallet_id: int
    crypto_id: int
    amount: Decimal
    address: str
    network_id: int

class DepositAddressSchema(Schema):
    wallet_id: int
    crypto_id: int
    network_id: int

class TransferRequestSchema(Schema):
    from_wallet_id: int
    to_wallet_id: int
    crypto_id: int
    amount: Decimal


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

    # Initialize WalletBalance for each cryptocurrency
    cryptocurrencies = Cryptocurrency.objects.all()
    WalletBalance.objects.bulk_create([
        WalletBalance(wallet=wallet, cryptocurrency=crypto, balance=0.0)
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
        user_wallet_balance_instances = WalletBalance.objects.filter(wallet=wallet).select_related('cryptocurrency', 'network')
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


@router.get('/getWalletBalance', response=List[WalletBalanceSchema])
def get_wallet_balance(request):
    """Get all wallet balances."""
    balances = WalletBalance.objects.all()
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



@router.get('/wallet/{wallet_id}/balances', response=List[WalletBalanceSchema])
def get_wallet_balances(request, wallet_id: int):
    """Get all cryptocurrency balances for a specific wallet."""
    wallet = get_object_or_404(Wallet, id=wallet_id)
    balances = WalletBalance.objects.filter(wallet=wallet)
    return [
        {
            "wallet_id": balance.wallet.id,
            "crypto_id": balance.cryptocurrency.id,
            "balance": balance.balance
        } for balance in balances
    ]

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
def withdraw(request, form: WithdrawRequestSchema):
    """Withdraw cryptocurrency from wallet."""
    wallet = get_object_or_404(Wallet, id=form.wallet_id)
    crypto = get_object_or_404(Cryptocurrency, id=form.crypto_id)
    network = get_object_or_404(Network, id=form.network_id)
    
    # Check if wallet has enough balance
    try:
        wallet_balance = WalletBalance.objects.get(wallet=wallet, cryptocurrency=crypto)
    except WalletBalance.DoesNotExist:
        return {"error": "No balance found for this cryptocurrency"}
    
    if wallet_balance.balance < form.amount:
        return {"error": "Insufficient balance"}
    
    # Calculate fee (example: 0.1% of transaction amount)
    fee = form.amount * Decimal('0.001')
    
    # Create transaction record
    transaction = Transaction.objects.create(
        type="withdraw",
        amount=form.amount,
        fee=fee,
        status="pending"
    )
    transaction.wallet_id.add(wallet)
    
    # Update wallet balance (will be actually deducted when transaction is confirmed)
    wallet_balance.balance -= (form.amount + fee)
    wallet_balance.save()
    
    return {
        "success": True,
        "transaction_id": transaction.id,
        "amount": form.amount,
        "fee": fee,
        "status": "pending"
    }

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
        from_balance = WalletBalance.objects.get(wallet=from_wallet, cryptocurrency=crypto)
    except WalletBalance.DoesNotExist:
        return {"error": "No balance found for this cryptocurrency in source wallet"}
    
    if from_balance.balance < form.amount:
        return {"error": "Insufficient balance"}
    
    # Get or create destination wallet balance
    to_balance, created = WalletBalance.objects.get_or_create(
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