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

class SendRequestSchema(Schema):
    wallet_id: int
    crypto_id: int
    network_id: int
    amount: Decimal
    recipient_address: str
    memo: Optional[str] = None  # Optional memo/tag field for certain blockchains


# Endpoints
@router.get('/getWallet/')
def get_user_wallet(request, user_id: int):
    wallet_instance = Wallet.objects.filter(user_id=user_id).first()
    if not wallet_instance:
        return []

    user_wallet_balance_instances = WalletBalance.objects.filter(wallet=wallet_instance).select_related('cryptocurrency')

    response_data = [
        {
            "wallet_id": wallet_instance.id,
            "crypto_id": balance.cryptocurrency.id if balance.cryptocurrency else 0,
            "crypto_name": balance.cryptocurrency.name if balance.cryptocurrency else "Unknown",
            "crypto_symbol": balance.cryptocurrency.symbol if balance.cryptocurrency else "N/A",
            "crypto_description": balance.cryptocurrency.crypto_description if balance.cryptocurrency else "No description available",
            "network": balance.network.name if balance.network else "Unknown",
            "balance": float(balance.balance) if balance.balance != 0 else 0.0
        }
        for balance in user_wallet_balance_instances
    ]
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
        wallet_balance = WalletBalance.objects.get(
            wallet=wallet, 
            cryptocurrency=crypto,
            network=network
        )
    except WalletBalance.DoesNotExist:
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