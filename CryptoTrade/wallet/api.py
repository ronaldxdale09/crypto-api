from ninja import Router
from crypto_currency.models import *
from user_account.models import *
from .models import *
from .forms import *
router = Router()


@router.get('/getWalletBalance', response=list[WalletBalanceSchema])
def get_wallet_balance(request):
    return WalletBalance.objects.all()
