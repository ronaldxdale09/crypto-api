from ninja import Schema
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

# Only import what you need from models, don't import * as it can cause issues
# from .models import * - Don't do this

# Basic schemas
class WalletBalanceSchema(Schema):
    wallet_id: int
    crypto_id: int
    network: str
    balance: Decimal

class WalletSchema(Schema):
    id: int
    available_balance: Decimal
    wallet_address: Optional[str] = None
    is_active: bool

class TransactionSchema(Schema):
    id: int
    type: str
    amount: Decimal
    fee: Decimal
    status: str
    timestamp: Optional[datetime] = None

# Request schemas
class WithdrawRequestSchema(Schema):
    wallet_id: int
    crypto_id: int
    amount: Decimal
    address: str
    network_id: int

class DepositAddressRequestSchema(Schema):
    wallet_id: int
    crypto_id: int
    network_id: int

class TransferRequestSchema(Schema):
    from_wallet_id: int
    to_wallet_id: int
    crypto_id: int
    amount: Decimal

# New schema for send functionality
class SendRequestSchema(Schema):
    wallet_id: int
    crypto_id: int
    network_id: int
    amount: Decimal
    recipient_address: str
    memo: Optional[str] = None  # Optional memo/tag field for certain blockchains

# Response schemas
class TransactionResponseSchema(Schema):
    success: bool
    transaction_id: int
    tx_hash: Optional[str] = None
    amount: Decimal
    fee: Decimal
    recipient: Optional[str] = None
    crypto: Optional[str] = None
    network: Optional[str] = None
    status: str
    estimated_completion_time: Optional[str] = None

class NetworkFeeSchema(Schema):
    cryptocurrency: str
    network: str
    fee_options: dict
    updated_at: str