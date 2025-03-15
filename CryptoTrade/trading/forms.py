from ninja import Schema
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

# Base schemas
class OrderSchema(Schema):
    id: int
    user_id: int
    cryptocurrency_id: int
    order_type: str  # 'buy' or 'sell'
    execution_type: str  # 'market' or 'limit'
    price: Decimal
    amount: Decimal
    total_in_usdt: Optional[Decimal] = None
    trade_fee: Optional[Decimal] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    external_order_id: Optional[int] = None

class TradeSchema(Schema):
    id: int
    buyer_id: int
    cryptocurrency_id: int
    price: Decimal
    amount: Decimal
    fee: Decimal
    executed_at: datetime

class TradingPairSchema(Schema):
    id: int
    base_currency_id: int
    quote_currency_id: int
    base_symbol: str
    quote_symbol: str
    is_active: bool
    external_pair_id: Optional[int] = None

# Request schemas
class BuySellSchema(Schema):
    currentPrice: Decimal
    amount: Decimal
    wallet_id: int  # Now required as per API requirements
    execution_type: str = 'market'  # Default but required in API

class CancelOrderSchema(Schema):
    user_id: int  # For security validation

# Response schemas
class BuySellResponseSchema(Schema):
    success: bool
    external_order_id: Optional[int] = None
    transaction_details: Optional[dict] = None
    wallet_details: Optional[dict] = None
    external_api_response: Optional[dict] = None
    error: Optional[str] = None

class MarketDataSchema(Schema):
    pair_id: int
    pair_name: str
    current_price: Decimal
    high_24h: Decimal
    low_24h: Decimal
    volume_24h: Decimal
    change_24h: Decimal