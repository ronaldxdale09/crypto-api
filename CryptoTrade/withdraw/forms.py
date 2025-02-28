from ninja import Schema
from wallet.models import *
from user_account.models import *
from crypto_currency.models import *

class WithdrawSchema(Schema):
    amount:str