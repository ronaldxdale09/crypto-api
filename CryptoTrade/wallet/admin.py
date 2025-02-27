from django.contrib import admin

# Register your models here.
from django.contrib import admin
from wallet.models import *

# Register your models here.

admin.site.register(Wallet)
admin.site.register(WalletAddress)
admin.site.register(Transaction)
admin.site.register(WalletBalance)
