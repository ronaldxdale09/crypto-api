from ninja import Router
from .models import *
from .forms import *
router = Router()

@router.get('/getUser', response=list[UserSchema])
def get_user(request):
    return User.objects.all()