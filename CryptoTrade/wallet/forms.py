from .models import *
from ninja import Schema


class WalletBalanceSchema(Schema):
    wallet_id:int
    crypto_id:int
    balance:int