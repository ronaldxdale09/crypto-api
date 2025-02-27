from django.contrib import admin

# Register your models here.

from crypto_currency.models import *

# Register your models here.

admin.site.register(Network)
admin.site.register(Cryptocurrency)
