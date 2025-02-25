from ninja import NinjaAPI
from user_account.api import router as user_account_router
from wallet.api import router as wallet_router
from crypto_currency.api import router as cryptoCurrency_router
from deposit.api import router as deposit_router
# from supabase import create_client
from django.conf import settings


# supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
api = NinjaAPI()

api.add_router("/user_account/", user_account_router)
api.add_router("/wallet", wallet_router)
api.add_router("/crypto_currency", cryptoCurrency_router)
api.add_router("/deposit", deposit_router)


