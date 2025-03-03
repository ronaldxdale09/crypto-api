from .models import *
from ninja import Schema
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

# Basic wallet schemas
class WalletBalanceSchema(Schema):
    wallet_id: int
    crypto_id: int
    balance: Decimal

class WalletSchema(Schema):
    id: int
    available_balance: Decimal
    wallet_address: Optional[str] = None
    is_active: bool

# Transaction schemas
class TransactionSchema(Schema):
    id: int
    type: str
    amount: Decimal
    fee: Decimal
    status: str
    timestamp: Optional[datetime] = None

class TransactionListSchema(Schema):
    transactions: List[TransactionSchema]
    count: int

# Request schemas for operations
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

# Response schemas
class WithdrawResponseSchema(Schema):
    success: bool
    transaction_id: int
    amount: Decimal
    fee: Decimal
    status: str

class DepositAddressResponseSchema(Schema):
    success: bool
    wallet_id: int
    crypto: str
    network: str
    address: str

class TransferResponseSchema(Schema):
    success: bool
    transaction_id: int
    amount: Decimal
    from_wallet: int
    to_wallet: int
    status: str

# Market data schemas
class CryptoPriceSchema(Schema):
    crypto_id: int
    symbol: str
    price_usd: float
    change_24h: Optional[float] = None
    updated_at: str

class MarketPriceListSchema(Schema):
    prices: List[CryptoPriceSchema]

# Wallet operations schemas
class WalletOperationResultSchema(Schema):
    success: bool
    wallet_id: int
    operation: str
    details: Optional[dict] = None

# User wallet schema
class UserWalletListSchema(Schema):
    user_id: int
    wallets: List[WalletSchema]
    count: int