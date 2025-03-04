from .models import *
from ninja import Schema
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

class ShowCryptoCurrencySchema(Schema):
    id: int
    symbol: str
    crypto_description: str