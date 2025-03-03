from ninja import Router
from crypto_currency.models import *
from user_account.models import *
from .models import *
from .forms import *
from typing import List
from decimal import Decimal
from django.shortcuts import get_object_or_404
import uuid

router = Router()

# Get wallet balance
@router.get('/getWalletBalance', response=List[WalletBalanceSchema])
def get_wallet_balance(request):
    """Get all wallet balances"""
    balances = WalletBalance.objects.all()
    return [
        {
            "wallet_id": balance.wallet.id,
            "crypto_id": balance.cryptocurrency.id,
            "balance": balance.balance
        } for balance in balances
    ]

# Get wallet by ID
@router.get('/wallet/{wallet_id}', response=WalletSchema)
def get_wallet(request, wallet_id: int):
    """Get wallet information by ID"""
    wallet = get_object_or_404(Wallet, id=wallet_id)
    return {
        "id": wallet.id,
        "available_balance": wallet.available_balance,
        "wallet_address": wallet.wallet_address,
        "is_active": wallet.is_active
    }

# Get wallet balances for a specific wallet
@router.get('/wallet/{wallet_id}/balances', response=List[WalletBalanceSchema])
def get_wallet_balances(request, wallet_id: int):
    """Get all cryptocurrency balances for a specific wallet"""
    wallet = get_object_or_404(Wallet, id=wallet_id)
    balances = WalletBalance.objects.filter(wallet=wallet)
    return [
        {
            "wallet_id": balance.wallet.id,
            "crypto_id": balance.cryptocurrency.id,
            "balance": balance.balance
        } for balance in balances
    ]

# Get transactions for a specific wallet
@router.get('/wallet/{wallet_id}/transactions', response=List[TransactionSchema])
def get_wallet_transactions(request, wallet_id: int):
    """Get all transactions for a specific wallet"""
    wallet = get_object_or_404(Wallet, id=wallet_id)
    transactions = Transaction.objects.filter(wallet_id=wallet).order_by('-timestamp')
    return [
        {
            "id": tx.id,
            "type": tx.type,
            "amount": tx.amount,
            "fee": tx.fee,
            "status": tx.status,
            "timestamp": tx.timestamp
        } for tx in transactions
    ]

# Withdraw cryptocurrency
@router.post('/withdraw')
def withdraw(request, form: WithdrawRequestSchema):
    """Withdraw cryptocurrency from wallet"""
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
        status="pending",
        destination_address=form.address
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

# Get deposit address
@router.post('/deposit/address')
def get_deposit_address(request, form: DepositAddressRequestSchema):
    """Get or create deposit address for a cryptocurrency and network"""
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

# Transfer cryptocurrency between wallets
@router.post('/transfer')
def transfer_crypto(request, form: TransferRequestSchema):
    """Transfer cryptocurrency between wallets"""
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

# Get user wallets
@router.get('/user/{user_id}/wallets')
def get_user_wallets(request, user_id: int):
    """Get all wallets for a specific user"""
    user = get_object_or_404(User, id=user_id)
    wallets = Wallet.objects.filter(user_id=user)
    
    return {
        "user_id": user_id,
        "wallets": [
            {
                "id": wallet.id,
                "available_balance": wallet.available_balance,
                "wallet_address": wallet.wallet_address,
                "is_active": wallet.is_active
            } for wallet in wallets
        ],
        "count": wallets.count()
    }

# Toggle wallet active status
@router.post('/wallet/{wallet_id}/toggle-active')
def toggle_wallet_active(request, wallet_id: int):
    """Enable or disable a wallet"""
    wallet = get_object_or_404(Wallet, id=wallet_id)
    wallet.is_active = not wallet.is_active
    wallet.save()
    
    return {
        "success": True,
        "wallet_id": wallet.id,
        "is_active": wallet.is_active,
        "status": "enabled" if wallet.is_active else "disabled"
    }

# Get all transactions
@router.get('/transactions', response=List[TransactionSchema])
def get_all_transactions(request):
    """Get all transactions"""
    transactions = Transaction.objects.all().order_by('-timestamp')
    return [
        {
            "id": tx.id,
            "type": tx.type,
            "amount": tx.amount,
            "fee": tx.fee,
            "status": tx.status,
            "timestamp": tx.timestamp
        } for tx in transactions
    ]
