# crypto_currency/api.py - Updated with Chart API

from ninja import Router
from .models import *
from .forms import *
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings
from django.shortcuts import get_object_or_404
import json
import random

# Global logo paths dictionary for cryptocurrencies
CRYPTO_LOGO_PATHS = {
    "BTC": "https://shorturl.at/jbnPp",
    "DOGE": "https://iimbltovdjhoifnmzims.supabase.co/storage/v1/object/sign/crypto_app/crypto/Dogecoin.png?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJjcnlwdG9fYXBwL2NyeXB0by9Eb2dlY29pbi5wbmciLCJpYXQiOjE3NDExMDA0NzgsImV4cCI6MTc0OTY1NDA3OH0.uupInNHoBmUoa-s-EhNcnthZBz_1nbwIum1goCd0KW8",
    "ETH": "https://iimbltovdjhoifnmzims.supabase.co/storage/v1/object/sign/crypto_app/crypto/ethereum.png?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJjcnlwdG9fYXBwL2NyeXB0by9ldGhlcmV1bS5wbmciLCJpYXQiOjE3NDExMDA1MDMsImV4cCI6MTc0OTY1NDEwM30.prgNNelliJr75t8RTFC1u--DSWDJBCS0A9HSTiZz2Ew",
    "SOL": "https://iimbltovdjhoifnmzims.supabase.co/storage/v1/object/sign/crypto_app/crypto/Solana.png?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJjcnlwdG9fYXBwL2NyeXB0by9Tb2xhbmEucG5nIiwiaWF0IjoxNzQxMTAwNTI3LCJleHAiOjE3NDk2NTQxMjd9.VbbJ14SUdI6sw0st83Bli9YNHOH4Da-LRln5e2vulWs",
    "XRP": "https://iimbltovdjhoifnmzims.supabase.co/storage/v1/object/sign/crypto_app/crypto/XRP.png?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJjcnlwdG9fYXBwL2NyeXB0by9YUlAucG5nIiwiaWF0IjoxNzQxMTAwNTUwLCJleHAiOjE3NDk2NTQxNTB9.LMoEs_Wqvj5KbprILXSJQSLmRGZUYtqHB7ZOv2xRQoQ"
}

# Global coin names dictionary
COIN_NAMES = {
    "BTC": "Bitcoin",
    "DOGE": "Dogecoin", 
    "ETH": "Ethereum",
    "SOL": "Solana",
    "XRP": "XRP"
}

# Function to provide placeholder prices for testing
def get_placeholder_price(symbol):
    """Return a reasonable placeholder price for each cryptocurrency"""
    price_map = {
        "BTC": Decimal('30000.00'),
        "ETH": Decimal('2000.00'),
        "DOGE": Decimal('0.10'),
        "SOL": Decimal('100.00'),
        "XRP": Decimal('0.50')
    }
    return price_map.get(symbol, Decimal('1.00'))

# Helper function to get logo URL for a cryptocurrency
def get_crypto_logo(symbol):
    """Get the logo URL for a cryptocurrency symbol"""
    return CRYPTO_LOGO_PATHS.get(symbol, "")

router = Router()

# FreeCryptoAPI configuration
API_BASE_URL = "https://api.freecryptoapi.com/v1"
API_KEY = "gbkiifey6fo94cbnvpw3"  # Replace with your API key or store in settings

def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

# Initialize price history data collection (call once from view or API)
def initialize_price_history():
    """Initialize price history for all cryptocurrencies if none exists"""
    # Check if we have any price history
    if PriceHistory.objects.count() == 0:
        # Collect initial price data
        collect_price_data()

def collect_price_data():
    """
    Collect current price data for all cryptocurrencies and store in PriceHistory
    This function can be called manually or by a scheduled task
    """
    cryptocurrencies = Cryptocurrency.objects.filter(is_tradable=True)
    symbols = [crypto.symbol for crypto in cryptocurrencies]
    
    # Skip if no cryptocurrencies
    if not symbols:
        return
    
    # Build symbols string for API
    symbols_param = "+".join(symbols)
    
    try:
        # Call API to get latest prices
        response = requests.get(
            f"{API_BASE_URL}/getData?symbol={symbols_param}", 
            headers=get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            result_data = data.get('result', {})
            
            current_time = datetime.now()
            price_history_records = []
            
            # Process each cryptocurrency
            for crypto in cryptocurrencies:
                if crypto.symbol in result_data:
                    crypto_data = result_data[crypto.symbol]
                    
                    if 'price' in crypto_data:
                        price = Decimal(str(crypto_data.get('price', 0)))
                        
                        # Update cryptocurrency price
                        crypto.price = price
                        crypto.last_updated = current_time
                        crypto.save()
                        
                        # Create price history record
                        price_history_records.append(
                            PriceHistory(
                                cryptocurrency=crypto,
                                timestamp=current_time,
                                price=price
                            )
                        )
                else:
                    # Use placeholder price if API doesn't return data
                    price = get_placeholder_price(crypto.symbol)
                    # Update with placeholder
                    crypto.price = price
                    crypto.last_updated = current_time
                    crypto.save()
                    
                    # Create price history record with placeholder
                    price_history_records.append(
                        PriceHistory(
                            cryptocurrency=crypto,
                            timestamp=current_time,
                            price=price
                        )
                    )
            
            # Bulk create price history records
            if price_history_records:
                PriceHistory.objects.bulk_create(price_history_records)
                
            return True
    except Exception as e:
        print(f"Error collecting price data: {str(e)}")
        return False

@router.get('/getCryptocurrencies', response=List[ShowCryptoCurrencySchema])
def get_cryptocurrencies(request):
    """Get list of available cryptocurrencies"""
    # Define the specific coins we want to focus on
    focus_coins = ["BTC", "DOGE", "ETH", "SOL", "XRP"]
    
    try:
        # Check if we have these coins in our database already
        for symbol in focus_coins:
            if not Cryptocurrency.objects.filter(symbol=symbol).exists():
                # Create the coin if it doesn't exist
                Cryptocurrency.objects.create(
                    symbol=symbol,
                    id_pk=symbol.lower(),
                    name=COIN_NAMES.get(symbol, symbol),
                    is_tradable=True,
                    crypto_description=f"{COIN_NAMES.get(symbol, symbol)} cryptocurrency",
                    logo_path=get_crypto_logo(symbol),
                    price=Decimal('0.0'),
                    price_change_24h=Decimal('0.0')
                )
            else:
                # Make sure existing coins have all required data
                crypto = Cryptocurrency.objects.get(symbol=symbol)
                updated = False
                
                if not crypto.logo_path:
                    crypto.logo_path = get_crypto_logo(symbol)
                    updated = True
                    
                if not crypto.name or crypto.name == "null":
                    crypto.name = COIN_NAMES.get(symbol, symbol)
                    updated = True
                    
                if not crypto.price:
                    crypto.price = Decimal('0.0')
                    updated = True
                    
                if not crypto.price_change_24h:
                    crypto.price_change_24h = Decimal('0.0')
                    updated = True
                    
                if updated:
                    crypto.save()
        
        # Try to fetch fresh data from the API for our focus coins
        symbols_param = "+".join(focus_coins)
        response = requests.get(
            f"{API_BASE_URL}/getData?symbol={symbols_param}", 
            headers=get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            result_data = data.get('result', {})
            
            # Update each coin with fresh data
            for symbol in focus_coins:
                crypto = Cryptocurrency.objects.get(symbol=symbol)
                
                if symbol in result_data:
                    crypto_data = result_data[symbol]
                    
                    # Update with API data if available
                    if 'price' in crypto_data:
                        crypto.price = Decimal(str(crypto_data.get('price', 0)))
                    if 'change24h' in crypto_data:
                        crypto.price_change_24h = Decimal(str(crypto_data.get('change24h', 0)))
                    if 'marketCap' in crypto_data:
                        crypto.market_cap = Decimal(str(crypto_data.get('marketCap', 0)))
                    if 'volume24h' in crypto_data:
                        crypto.volume_24h = Decimal(str(crypto_data.get('volume24h', 0)))
                else:
                    # If API didn't return data for this coin, ensure we have at least placeholder values
                    if not crypto.price:
                        crypto.price = get_placeholder_price(symbol)
                    if not crypto.price_change_24h:
                        crypto.price_change_24h = Decimal(str(random.uniform(-5.0, 5.0)))
                
                # Make sure name is never null
                if not crypto.name or crypto.name == "null":
                    crypto.name = COIN_NAMES.get(symbol, symbol)
                    
                crypto.last_updated = datetime.now()
                crypto.save()

                # Add price history record
                PriceHistory.objects.create(
                    cryptocurrency=crypto,
                    timestamp=datetime.now(),
                    price=crypto.price
                )
        
        # Return data from database for our focus coins
        cryptocurrency_instances = Cryptocurrency.objects.filter(symbol__in=focus_coins)
        
        return [
            ShowCryptoCurrencySchema(
                id=crypto.id,
                symbol=crypto.symbol,
                name=crypto.name,
                price=round(crypto.price, 2),
                price_change_24h=crypto.price_change_24h,
                crypto_description=crypto.crypto_description or f"{crypto.name} cryptocurrency",
                logo_path=get_crypto_logo(crypto.symbol)
            )
            for crypto in cryptocurrency_instances
        ]
    except Exception as e:
        # If API fails, return what's in the database
        cryptocurrency_instances = Cryptocurrency.objects.filter(symbol__in=focus_coins)
        
        return [
            ShowCryptoCurrencySchema(
                id=crypto.id,
                symbol=crypto.symbol,
                name=crypto.name,
                price=round(crypto.price, 2),  # Round to 2 decimal places
                price_change_24h=crypto.price_change_24h,
                crypto_description=crypto.crypto_description or f"{crypto.name} cryptocurrency",
                logo_path=get_crypto_logo(crypto.symbol)
            )
            for crypto in cryptocurrency_instances
        ]

@router.get('/getCoinDetails/{symbol}', response=DetailedCryptoCurrencySchema)
def get_coin_details(request, symbol: str):
    """Get detailed information about a specific cryptocurrency including its networks"""
    symbol = symbol.upper()
    
    # First check if we have the coin in our database
    try:
        crypto = Cryptocurrency.objects.get(symbol=symbol)
    except Cryptocurrency.DoesNotExist:
        # If not in DB, create basic entry that we'll update with API data
        crypto = Cryptocurrency.objects.create(
            symbol=symbol,
            id_pk=symbol.lower(),
            name=COIN_NAMES.get(symbol, symbol),
            is_tradable=True,
            logo_path=get_crypto_logo(symbol),
            price=get_placeholder_price(symbol),
            price_change_24h=Decimal(str(random.uniform(-5.0, 5.0)))
        )
    
    try:
        # Get fresh data from the API
        response = requests.get(
            f"{API_BASE_URL}/getData?symbol={symbol}",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            coin_data = data.get('result', {}).get(symbol, {})
            
            if coin_data:
                # Update database with fresh data
                crypto.price = Decimal(str(coin_data.get('price', 0)))
                crypto.price_change_24h = Decimal(str(coin_data.get('change24h', 0)))
                crypto.market_cap = Decimal(str(coin_data.get('marketCap', 0)))
                crypto.volume_24h = Decimal(str(coin_data.get('volume24h', 0)))
                crypto.last_updated = datetime.now()
                crypto.save()
                
                # Update price history
                PriceHistory.objects.create(
                    cryptocurrency=crypto,
                    timestamp=datetime.now(),
                    price=crypto.price
                )
        
        # Get networks for this cryptocurrency
        crypto_networks = CryptocurrencyNetwork.objects.filter(
            cryptocurrency=crypto,
            network__is_active=True
        ).select_related('network')
        
        networks = [
            NetworkSchema(
                id=cn.network.id,
                name=cn.network.name,
                acronym=cn.network.acronym,
                description=cn.network.network_description,
                logo_path=cn.network.logo_path,  # Keep network logo as is
                withdrawal_fee=cn.withdrawal_fee,
                min_withdrawal=cn.min_withdrawal,
                is_withdrawal_enabled=cn.is_withdrawal_enabled
            ) for cn in crypto_networks
        ]
        
        # Return detailed data
        return DetailedCryptoCurrencySchema(
            id=crypto.id,
            symbol=crypto.symbol,
            name=crypto.name,
            price=crypto.price,
            price_change_24h=crypto.price_change_24h,
            market_cap=crypto.market_cap,
            volume_24h=crypto.volume_24h,
            last_updated=crypto.last_updated,
            crypto_description=crypto.crypto_description or f"{crypto.name} cryptocurrency",
            is_tradable=crypto.is_tradable,
            logo_path=get_crypto_logo(crypto.symbol),
            networks=networks
        )
    
    except Exception as e:
        # Get networks for this cryptocurrency even if API call fails
        crypto_networks = CryptocurrencyNetwork.objects.filter(
            cryptocurrency=crypto,
            network__is_active=True
        ).select_related('network')
        
        networks = [
            NetworkSchema(
                id=cn.network.id,
                name=cn.network.name,
                acronym=cn.network.acronym,
                description=cn.network.network_description,
                logo_path=cn.network.logo_path,  # Keep network logo as is
                withdrawal_fee=cn.withdrawal_fee,
                min_withdrawal=cn.min_withdrawal,
                is_withdrawal_enabled=cn.is_withdrawal_enabled
            ) for cn in crypto_networks
        ]
        
        # If API call fails, return what we have in the database
        return DetailedCryptoCurrencySchema(
            id=crypto.id,
            symbol=crypto.symbol,
            name=crypto.name,
            price=crypto.price,
            price_change_24h=crypto.price_change_24h,
            market_cap=crypto.market_cap,
            volume_24h=crypto.volume_24h,
            last_updated=crypto.last_updated,
            crypto_description=crypto.crypto_description or f"{crypto.name} cryptocurrency",
            is_tradable=crypto.is_tradable,
            logo_path=get_crypto_logo(crypto.symbol),
            networks=networks
        )

@router.get('/getAssets/{user_id}', response=List[DetailedCryptoCurrencySchema])
def get_user_assets(request, user_id: int):
    """Get cryptocurrencies owned by the user with balances"""
    try:
        from wallet.models import Wallet, WalletBalance
        
        # Get the user's wallet and balances
        wallet = Wallet.objects.filter(user_id=user_id).first()
        if not wallet:
            return []
            
        # Get balances with non-zero amounts
        balances = WalletBalance.objects.filter(wallet=wallet, balance__gt=0)
        
        result = []
        for balance in balances:
            crypto = balance.cryptocurrency
            
            # Try to get fresh price data if needed
            if not crypto.price or not crypto.last_updated or crypto.last_updated < datetime.now() - timedelta(hours=1):
                try:
                    # Fetch fresh price data
                    response = requests.get(
                        f"{API_BASE_URL}/getData?symbol={crypto.symbol}",
                        headers=get_headers()
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        coin_data = data.get('result', {}).get(crypto.symbol, {})
                        
                        if coin_data:
                            crypto.price = Decimal(str(coin_data.get('price', 0)))
                            crypto.price_change_24h = Decimal(str(coin_data.get('change24h', 0)))
                            crypto.last_updated = datetime.now()
                            crypto.save()
                            
                            # Add price history record
                            PriceHistory.objects.create(
                                cryptocurrency=crypto,
                                timestamp=datetime.now(),
                                price=crypto.price
                            )
                except Exception:
                    # If API call fails, continue with existing data
                    pass
            
            result.append(
                DetailedCryptoCurrencySchema(
                    id=crypto.id,
                    symbol=crypto.symbol,
                    name=crypto.name,
                    price=crypto.price,
                    price_change_24h=crypto.price_change_24h,
                    market_cap=crypto.market_cap,
                    volume_24h=crypto.volume_24h,
                    last_updated=crypto.last_updated,
                    crypto_description=crypto.crypto_description,
                    is_tradable=crypto.is_tradable,
                    logo_path=get_crypto_logo(crypto.symbol)
                )
            )
        
        return result
    except Exception as e:
        # Return empty list on error
        return []

@router.get('/getPriceHistory/{symbol}/{timeframe}', response=PriceHistorySchema)
def get_price_history(request, symbol: str, timeframe: str):
    """Get historical price data for a cryptocurrency
    timeframe options: 1h, 24h, 1w, 1m, 6m, 1y, all
    """
    crypto = get_object_or_404(Cryptocurrency, symbol=symbol.upper())
    
    try:
        # Map timeframe to days for API request
        days_map = {
            "1h": 1,      # Just use 1 day but will filter later
            "24h": 1,
            "1w": 7,
            "1m": 30,
            "6m": 180,
            "1y": 365,
            "all": 1825    # 5 years
        }
        days = days_map.get(timeframe, 7)  # Default to 1 week
        
        # Get historical data from API
        response = requests.get(
            f"{API_BASE_URL}/getHistory?symbol={symbol}&days={days}",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            history_data = data.get('result', {}).get(symbol.upper(), {})
            
            # Parse and convert the historical data
            history = []
            if history_data:
                for point in history_data:
                    timestamp = datetime.fromtimestamp(point.get('timestamp', 0))
                    price = Decimal(str(point.get('price', 0)))
                    
                    # Filter for 1h timeframe
                    if timeframe == "1h" and timestamp < datetime.now() - timedelta(hours=1):
                        continue
                        
                    history.append(
                        PriceHistoryPointSchema(
                            timestamp=timestamp,
                            price=price
                        )
                    )
                    
                    # Optionally store in database for future use
                    PriceHistory.objects.create(
                        cryptocurrency=crypto,
                        timestamp=timestamp,
                        price=price
                    )
            
            return PriceHistorySchema(
                cryptocurrency_id=crypto.id,
                symbol=crypto.symbol,
                history=history
            )
        
        # If API request fails, try to get data from database
        raise Exception("API request failed")
        
    except Exception as e:
        # Get data from database as fallback
        if timeframe == "1h":
            time_threshold = datetime.now() - timedelta(hours=1)
        elif timeframe == "24h":
            time_threshold = datetime.now() - timedelta(days=1)
        elif timeframe == "1w":
            time_threshold = datetime.now() - timedelta(weeks=1)
        elif timeframe == "1m":
            time_threshold = datetime.now() - timedelta(days=30)
        elif timeframe == "6m":
            time_threshold = datetime.now() - timedelta(days=180)
        elif timeframe == "1y":
            time_threshold = datetime.now() - timedelta(days=365)
        else:  # "all"
            time_threshold = datetime.now() - timedelta(days=1825)  # 5 years
            
        history_points = PriceHistory.objects.filter(
            cryptocurrency=crypto,
            timestamp__gte=time_threshold
        ).order_by('timestamp')
        
        history = [
            PriceHistoryPointSchema(
                timestamp=point.timestamp,
                price=point.price
            )
            for point in history_points
        ]
        
        return PriceHistorySchema(
            cryptocurrency_id=crypto.id,
            symbol=crypto.symbol,
            history=history
        )

@router.post('/convertCrypto', response=ConversionResponseSchema)
def convert_crypto(request, conversion_data: ConversionRequestSchema):
    """Calculate crypto conversion from one currency to another"""
    from_symbol = conversion_data.from_symbol.upper()
    to_symbol = conversion_data.to_symbol.upper()
    amount = conversion_data.amount
    
    try:
        # Call the API to get conversion data
        response = requests.get(
            f"{API_BASE_URL}/getConversion?from={from_symbol}&to={to_symbol}&amount={amount}",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            
            if result:
                return ConversionResponseSchema(
                    from_symbol=from_symbol,
                    to_symbol=to_symbol,
                    from_amount=amount,
                    to_amount=Decimal(str(result.get('toAmount', 0))),
                    exchange_rate=Decimal(str(result.get('exchangeRate', 0)))
                )
        
        # If API fails, calculate manually using prices in database
        from_crypto = Cryptocurrency.objects.get(symbol=from_symbol)
        to_crypto = Cryptocurrency.objects.get(symbol=to_symbol)
        
        if from_crypto.price and to_crypto.price:
            exchange_rate = to_crypto.price / from_crypto.price
            to_amount = amount * exchange_rate
            
            return ConversionResponseSchema(
                from_symbol=from_symbol,
                to_symbol=to_symbol,
                from_amount=amount,
                to_amount=to_amount,
                exchange_rate=exchange_rate
            )
        
        # If manual calculation fails too
        return ConversionResponseSchema(
            from_symbol=from_symbol,
            to_symbol=to_symbol,
            from_amount=amount,
            to_amount=Decimal(0),
            exchange_rate=Decimal(0)
        )
        
    except Exception as e:
        # Return zeros on error
        return ConversionResponseSchema(
            from_symbol=from_symbol,
            to_symbol=to_symbol,
            from_amount=amount,
            to_amount=Decimal(0),
            exchange_rate=Decimal(0)
        )
    
@router.get('/getNetworks/{symbol}', response=List[NetworkSchema])
def get_networks(request, symbol: str):
    """Get available networks for a specific cryptocurrency"""
    try:
        cryptocurrency = Cryptocurrency.objects.get(symbol=symbol.upper())
        crypto_networks = CryptocurrencyNetwork.objects.filter(
            cryptocurrency=cryptocurrency,
            network__is_active=True
        ).select_related('network')
        
        return [
            NetworkSchema(
                id=cn.network.id,
                name=cn.network.name,
                acronym=cn.network.acronym,
                description=cn.network.network_description,
                logo_path=cn.network.logo_path,  # Keep network logo as is
                withdrawal_fee=cn.withdrawal_fee,
                min_withdrawal=cn.min_withdrawal,
                is_withdrawal_enabled=cn.is_withdrawal_enabled
            ) for cn in crypto_networks
        ]
    except Exception as e:
        # Return empty list on error
        return []
    
@router.get('/getNetworkDetails/{network_id}', response=NetworkDetailSchema)
def get_network_details(request, network_id: int, cryptocurrency_id: Optional[int] = None):
    """Get detailed information about a network, optionally for a specific cryptocurrency"""
    try:
        network = get_object_or_404(Network, id=network_id)
        
        if cryptocurrency_id:
            crypto_network = get_object_or_404(
                CryptocurrencyNetwork, 
                network_id=network_id,
                cryptocurrency_id=cryptocurrency_id
            )
        else:
            # Get first cryptocurrency using this network as fallback
            crypto_network = CryptocurrencyNetwork.objects.filter(
                network_id=network_id
            ).first()
            
            if not crypto_network:
                # If no cryptocurrencies use this network, return basic info
                return NetworkDetailSchema(
                    id=network.id,
                    name=network.name,
                    acronym=network.acronym,
                    description=network.network_description,
                    withdrawal_fee=Decimal('0'),
                    min_withdrawal=Decimal('0'),
                    is_deposit_enabled=False,
                    is_withdrawal_enabled=False,
                    deposit_confirmations=0
                )
        
        return NetworkDetailSchema(
            id=network.id,
            name=network.name,
            acronym=network.acronym,
            description=network.network_description,
            withdrawal_fee=crypto_network.withdrawal_fee,
            min_withdrawal=crypto_network.min_withdrawal,
            is_deposit_enabled=crypto_network.is_deposit_enabled,
            is_withdrawal_enabled=crypto_network.is_withdrawal_enabled,
            deposit_confirmations=crypto_network.deposit_confirmations
        )
    except Exception as e:
        # Return error response
        return {"error": str(e)}

@router.get('/getChartData/{symbol}/{timeframe}', response=ChartDataSchema)
def get_chart_data(request, symbol: str, timeframe: str):
    """
    Get formatted chart data for a specific cryptocurrency and timeframe
    
    timeframe options: 1h, 24h, 1w, 1m, 6m, 1y, all
    Returns data points and additional chart metadata like min/max values
    """
    symbol = symbol.upper()
    
    try:
        # Get the cryptocurrency
        crypto = get_object_or_404(Cryptocurrency, symbol=symbol)
        
        # Define timeframe durations
        timeframe_durations = {
            "1h": timedelta(hours=1),
            "24h": timedelta(days=1),
            "1w": timedelta(weeks=1),
            "1m": timedelta(days=30),
            "6m": timedelta(days=180),
            "1y": timedelta(days=365),
            "all": timedelta(days=1825)  # 5 years
        }
        
        duration = timeframe_durations.get(timeframe, timeframe_durations["24h"])
        start_time = datetime.now() - duration
        
        # Try to get actual price history from database
        price_history = PriceHistory.objects.filter(
            cryptocurrency=crypto,
            timestamp__gte=start_time
        ).order_by('timestamp')
        
        # Store the current price for this cryptocurrency
        if crypto.price:
            # Check if we already have a price record for this timestamp
            current_time = datetime.now()
            if not PriceHistory.objects.filter(
                cryptocurrency=crypto,
                timestamp__gte=current_time - timedelta(minutes=1)
            ).exists():
                # Create a new price history record
                PriceHistory.objects.create(
                    cryptocurrency=crypto,
                    timestamp=current_time,
                    price=crypto.price
                )
        
        # If we don't have enough data points, generate synthetic data
        data_points = []
        
        if price_history.count() > 5:
            # Use real data if we have enough points
            for point in price_history:
                # Convert timestamp to milliseconds since epoch for FlutterFlow
                ms_since_epoch = int(point.timestamp.timestamp() * 1000)
                
                data_points.append(
                    ChartDataPointSchema(
                        x=ms_since_epoch,
                        y=float(point.price)  # Convert Decimal to float
                    )
                )
        else:
            # Generate synthetic data based on current price
            # Determine appropriate number of points based on timeframe
            point_counts = {
                "1h": 60,      # One per minute
                "24h": 24,     # One per hour
                "1w": 7,       # One per day
                "1m": 30,      # One per day
                "6m": 180,     # One per day
                "1y": 52,      # One per week
                "all": 60      # Approx. one per month for 5 years
            }
            num_points = point_counts.get(timeframe, 24)
            
            # Get base price or use placeholder
            base_price = crypto.price or get_placeholder_price(symbol)
            
            # Generate appropriate timestamps
            timestamps = []
            time_interval = duration / num_points
            current_time = start_time
            
            for _ in range(num_points):
                timestamps.append(current_time)
                current_time += time_interval
            
            # Generate prices with realistic movement patterns
            # Start with current price and work backwards with random variations
            prices = [base_price]
            volatility = {
                "BTC": Decimal('0.02'),     # 2% volatility
                "ETH": Decimal('0.03'),     # 3% volatility
                "SOL": Decimal('0.05'),     # 5% volatility
                "DOGE": Decimal('0.08'),    # 8% volatility
                "XRP": Decimal('0.04')      # 4% volatility
            }.get(symbol, Decimal('0.04'))
            
            # Generate remaining prices with realistic trend
            for i in range(1, num_points):
                # Random change with slight trend bias
                change = Decimal(str(random.uniform(-float(volatility), float(volatility))))
                # Add trend bias based on price_change_24h if available
                if crypto.price_change_24h:
                    trend_bias = (crypto.price_change_24h / 100) / num_points
                    change += Decimal(str(trend_bias))
                
                # Calculate new price
                new_price = prices[-1] * (1 + change)
                # Ensure price doesn't go below zero
                prices.append(max(new_price, Decimal('0.00001')))
            
            # Reverse to get chronological order
            prices.reverse()
            
            # Create data points in FlutterFlow-friendly format
            for i, ts in enumerate(timestamps):
                # Convert timestamp to milliseconds since epoch for FlutterFlow
                ms_since_epoch = int(ts.timestamp() * 1000)
                
                data_points.append(
                    ChartDataPointSchema(
                        x=ms_since_epoch,
                        y=float(prices[i])  # Convert Decimal to float
                    )
                )
                
                # Optionally save synthetic data to database for future use
                PriceHistory.objects.create(
                    cryptocurrency=crypto,
                    timestamp=ts,
                    price=prices[i]
                )
        
        # Calculate min and max prices for chart scaling
        prices = [p.y for p in data_points]
        min_price = min(prices) if prices else 0.0
        max_price = max(prices) if prices else 0.0
        
        # Calculate percent change
        if len(prices) >= 2:
            start_price = prices[0]
            end_price = prices[-1]
            if start_price > 0:
                percent_change = ((end_price - start_price) / start_price) * 100
            else:
                percent_change = 0.0
        else:
            percent_change = float(crypto.price_change_24h or 0.0)
        
        return ChartDataSchema(
            data=data_points,
            min_price=min_price,
            max_price=max_price,
            percent_change=round(percent_change, 2)  # Round to 2 decimal places
        )
        
    except Exception as e:
        # Return empty dataset with error info in case of any exception
        print(f"Chart error: {str(e)}")
        return ChartDataSchema(
            data=[],
            min_price=0.0,
            max_price=0.0,
            percent_change=0.0
        )

@router.get('/getChartPreference/{user_id}/{cryptocurrency_id}', response=ChartPreferenceSchema)
def get_chart_preference(request, user_id: int, cryptocurrency_id: int):
    """Get user's chart preferences for a specific cryptocurrency"""
    try:
        preference = ChartPreference.objects.get(
            user_id=user_id,
            cryptocurrency_id=cryptocurrency_id
        )
        
        return ChartPreferenceSchema(
            user_id=user_id,
            cryptocurrency_id=cryptocurrency_id,
            default_timeframe=preference.default_timeframe,
            show_volume=preference.show_volume,
            chart_type=preference.chart_type
        )
    except ChartPreference.DoesNotExist:
        # Return default preferences if not found
        return ChartPreferenceSchema(
            user_id=user_id,
            cryptocurrency_id=cryptocurrency_id,
            default_timeframe="24h",
            show_volume=True,
            chart_type="line"
        )

@router.post('/saveChartPreference', response=ChartPreferenceSchema)
def save_chart_preference(request, preference_data: ChartPreferenceSchema):
    """Save user's chart preferences for a specific cryptocurrency"""
    try:
        preference, created = ChartPreference.objects.get_or_create(
            user_id=preference_data.user_id,
            cryptocurrency_id=preference_data.cryptocurrency_id,
            defaults={
                'default_timeframe': preference_data.default_timeframe,
                'show_volume': preference_data.show_volume,
                'chart_type': preference_data.chart_type
            }
        )
        
        if not created:
            # Update existing preference
            preference.default_timeframe = preference_data.default_timeframe
            preference.show_volume = preference_data.show_volume
            preference.chart_type = preference_data.chart_type
            preference.save()
        
        return preference_data
    except Exception as e:
        # Return the original data on error
        return preference_data