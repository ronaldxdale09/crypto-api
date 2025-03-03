from .models import *
from ninja import Schema
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

# Basic schemas
class WalletBalanceSchema(Schema):
    wallet_id: int
    crypto_id: int
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
