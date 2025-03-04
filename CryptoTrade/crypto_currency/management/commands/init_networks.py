from django.core.management.base import BaseCommand
from crypto_currency.models import Network, Cryptocurrency, CryptocurrencyNetwork
from decimal import Decimal

class Command(BaseCommand):
    help = 'Initialize blockchain networks and their relationships with cryptocurrencies'

    def handle(self, *args, **options):
        self.stdout.write('Creating basic blockchain networks...')
        
        # Create networks
        networks = [
            {
                "name": "Ethereum", 
                "acronym": "ERC20", 
                "description": "Ethereum Network (ERC-20)", 
                "logo_path": "/crypto/networks/ethereum.png"
            },
            {
                "name": "Binance Smart Chain", 
                "acronym": "BEP20", 
                "description": "Binance Smart Chain (BEP-20)", 
                "logo_path": "/crypto/networks/bsc.png"
            },
            {
                "name": "Bitcoin", 
                "acronym": "BTC", 
                "description": "Bitcoin Network", 
                "logo_path": "/crypto/networks/bitcoin.png"
            },
            {
                "name": "Solana", 
                "acronym": "SOL", 
                "description": "Solana Network", 
                "logo_path": "/crypto/networks/solana.png"
            },
            {
                "name": "Tron", 
                "acronym": "TRC20", 
                "description": "Tron Network (TRC-20)", 
                "logo_path": "/crypto/networks/tron.png"
            }
        ]
        
        # Create network objects
        created_networks = []
        for network_data in networks:
            network, created = Network.objects.update_or_create(
                name=network_data["name"],
                defaults={
                    "acronym": network_data["acronym"],
                    "network_description": network_data["description"],
                    "logo_path": network_data["logo_path"],
                    "is_active": True
                }
            )
            
            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f'{status} network: {network.name}'))
            created_networks.append(network)
        
        # Define network compatibility for each cryptocurrency
        crypto_network_map = {
            "BTC": ["Bitcoin"],
            "ETH": ["Ethereum", "Binance Smart Chain"],
            "DOGE": ["Bitcoin", "Binance Smart Chain"],
            "SOL": ["Solana"],
            "XRP": ["Tron"]
        }
        
        # Set default withdrawal fees and minimums
        withdrawal_fees = {
            ("BTC", "Bitcoin"): Decimal('0.0001'),
            ("ETH", "Ethereum"): Decimal('0.005'),
            ("ETH", "Binance Smart Chain"): Decimal('0.001'),
            ("DOGE", "Bitcoin"): Decimal('1'),
            ("DOGE", "Binance Smart Chain"): Decimal('0.5'),
            ("SOL", "Solana"): Decimal('0.01'),
            ("XRP", "Tron"): Decimal('0.25')
        }
        
        min_withdrawals = {
            ("BTC", "Bitcoin"): Decimal('0.001'),
            ("ETH", "Ethereum"): Decimal('0.01'),
            ("ETH", "Binance Smart Chain"): Decimal('0.01'),
            ("DOGE", "Bitcoin"): Decimal('10'),
            ("DOGE", "Binance Smart Chain"): Decimal('5'),
            ("SOL", "Solana"): Decimal('0.1'),
            ("XRP", "Tron"): Decimal('10')
        }
        
        # Connect cryptocurrencies with their compatible networks
        for symbol, network_names in crypto_network_map.items():
            try:
                crypto = Cryptocurrency.objects.get(symbol=symbol)
                
                for network_name in network_names:
                    try:
                        network = Network.objects.get(name=network_name)
                        
                        # Get default fee and minimum for this combination
                        fee = withdrawal_fees.get((symbol, network_name), Decimal('0.001'))
                        minimum = min_withdrawals.get((symbol, network_name), Decimal('0.01'))
                        
                        # Create or update the relationship
                        crypto_network, created = CryptocurrencyNetwork.objects.update_or_create(
                            cryptocurrency=crypto,
                            network=network,
                            defaults={
                                "is_deposit_enabled": True,
                                "is_withdrawal_enabled": True,
                                "withdrawal_fee": fee,
                                "min_withdrawal": minimum,
                                "deposit_confirmations": 6
                            }
                        )
                        
                        status = "Created" if created else "Updated"
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'{status} connection: {crypto.symbol} on {network.name}'
                            )
                        )
                    except Network.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'Network not found: {network_name}')
                        )
            except Cryptocurrency.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Cryptocurrency not found: {symbol}')
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully initialized networks'))