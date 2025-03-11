from ninja import Schema
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

# Base schemas
class OrderSchema(Schema):
    id: int
    user_id: int
    wallet_id: int
    crypto_id: int
    order_type: str  # 'buy' or 'sell'
    execution_type: str #'market' or 'limit'
    price: Decimal
    amount: Decimal
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

class TradeSchema(Schema):
    id: int
    buyer_id: int
    seller_id: int
    crypto_id: int
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

# Request schemas
class CreateOrderSchema(Schema):
    user_id: int
    wallet_id: int
    crypto_id: int
    order_type: str  # 'buy' or 'sell'
    execution_type: str # 'limit' or 'market'
    price: Decimal
    amount: Decimal

class CancelOrderSchema(Schema):
    order_id: int
    user_id: int  # For security validation

# Response schemas
class OrderResponseSchema(Schema):
    success: bool
    order: Optional[OrderSchema] = None
    error: Optional[str] = None

class OrderListResponseSchema(Schema):
    orders: List[OrderSchema]
    count: int

class TradeListResponseSchema(Schema):
    trades: List[TradeSchema]
    count: int

class TradingPairListResponseSchema(Schema):
    pairs: List[TradingPairSchema]
    count: int

class MarketDataSchema(Schema):
    pair_id: int
    pair_name: str
    current_price: Decimal
    high_24h: Decimal
    low_24h: Decimal
    volume_24h: Decimal
    change_24h: Decimal