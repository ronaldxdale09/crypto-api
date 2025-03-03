from .models import *
from ninja import Schema
from typing import List, Optional
<<<<<<< HEAD
=======
from decimal import Decimal
from datetime import datetime
>>>>>>> 218e8708f1f31a40e25c1e0d2bb2c0ed5e319b9d

# Basic schemas
class WalletBalanceSchema(Schema):
<<<<<<< HEAD
    wallet_id: Optional[int] = None
    crypto_id: Optional[int] = None
    network_id: Optional[int] = None
    balance: float
class WalletSchema(Schema):
    wallet_id: int
    balances: List[WalletBalanceSchema]
=======
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
>>>>>>> 218e8708f1f31a40e25c1e0d2bb2c0ed5e319b9d
