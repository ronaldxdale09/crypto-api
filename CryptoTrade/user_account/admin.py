from django.contrib import admin
from user_account.models import *

# Register your models here.

admin.site.register(User)
admin.site.register(Role)
admin.site.register(UserDetail)
admin.site.register(KnowYourCustomer)