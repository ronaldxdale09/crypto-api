from .models import *
from ninja import Schema
from typing import List, Optional


class WalletBalanceSchema(Schema):
    wallet_id: Optional[int] = None
    crypto_id: Optional[int] = None
    network_id: Optional[int] = None
    balance: float
class WalletSchema(Schema):
    wallet_id: int
    balances: List[WalletBalanceSchema]