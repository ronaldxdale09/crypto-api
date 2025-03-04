# crypto_currency/forms.py

from ninja import Schema
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

class NetworkSchema(Schema):
    id: int
    name: str
    acronym: Optional[str]
    description: Optional[str]
    logo_path: Optional[str]
    withdrawal_fee: Optional[Decimal]
    min_withdrawal: Optional[Decimal]
    is_withdrawal_enabled: bool = True

class ShowCryptoCurrencySchema(Schema):
    id: int
    symbol: str
    name: Optional[str]
    price: Optional[Decimal]
    price_change_24h: Optional[Decimal]
    crypto_description: Optional[str]
    logo_path: Optional[str]

class NetworkDetailSchema(Schema):
    id: int
    name: str
    acronym: Optional[str]
    description: Optional[str]
    withdrawal_fee: Decimal
    min_withdrawal: Decimal
    is_deposit_enabled: bool
    is_withdrawal_enabled: bool
    deposit_confirmations: int

class DetailedCryptoCurrencySchema(Schema):
    id: int
    symbol: str
    name: Optional[str] 
    price: Optional[Decimal]
    price_change_24h: Optional[Decimal]
    market_cap: Optional[Decimal]
    volume_24h: Optional[Decimal]
    last_updated: Optional[datetime]
    crypto_description: Optional[str]
    is_tradable: bool
    logo_path: Optional[str]
    networks: Optional[List[NetworkSchema]]
    
class PriceHistoryPointSchema(Schema):
    timestamp: datetime
    price: Decimal
    
class PriceHistorySchema(Schema):
    cryptocurrency_id: int
    symbol: str
    history: List[PriceHistoryPointSchema]
    
class ConversionRequestSchema(Schema):
    from_symbol: str
    to_symbol: str
    amount: Decimal
    
class ConversionResponseSchema(Schema):
    from_symbol: str
    to_symbol: str 
    from_amount: Decimal
    to_amount: Decimal
    exchange_rate: Decimal

class DepositAddressRequestSchema(Schema):
    cryptocurrency_id: int
    network_id: int

class DepositAddressResponseSchema(Schema):
    cryptocurrency_symbol: str
    network_name: str
    address: str
    
class WithdrawalRequestSchema(Schema):
    cryptocurrency_id: int
    network_id: int
    address: str
    amount: Decimal
    
class WithdrawalResponseSchema(Schema):
    id: int
    cryptocurrency_symbol: str
    network_name: str
    address: str
    amount: Decimal
    fee: Decimal
    status: str
    created_at: datetime