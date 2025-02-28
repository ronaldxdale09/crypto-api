from ninja import Router
from .models import *
from .forms import *
from decimal import Decimal
from django.shortcuts import get_object_or_404

router = Router()

# @router.post('/withdraw/user={user_id}')
