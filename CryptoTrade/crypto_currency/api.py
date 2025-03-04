from ninja import Router
from .models import *
from .forms import *

router = Router()

#add functionality

@router.get('/getCryptocurrencies', response=List[ShowCryptoCurrencySchema])
def get_cryptocurrencies(request):
    cryptocurrency_instances = Cryptocurrency.objects.all()

    return [
        ShowCryptoCurrencySchema(
            id=crypto.id,
            symbol=crypto.symbol,
            crypto_description=crypto.crypto_description if crypto.crypto_description else "No description available"
        )
        for crypto in cryptocurrency_instances
    ]

