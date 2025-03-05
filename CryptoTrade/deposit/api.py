from ninja import Router
from .models import *
from .forms import *
from decimal import Decimal
from django.shortcuts import get_object_or_404

router = Router()



@router.post('/deposit/user={user_id}/crypto={cryptocurrency_id}')
def deposit(request, user_id:int,cryptocurrency_id:int,form: DepositSchema):
    # Ensure amount is positive
    if form.amount <= 0:
        return {"error": "Deposit amount must be greater than 0"}

    # Get the user and their wallet
    user_instance = get_object_or_404(User, id=user_id)
    user_id = user_instance.id
    print(user_id)
    wallet_instance = Wallet.objects.filter(user_id=user_id).first()
    wallet_id = wallet_instance.id
    print(wallet_id)
    if not wallet_id:
        return {"error": "Wallet not found for this user"}
    
    # Get or create the UserAsset record
    wallet_balance= UserAsset.objects.get(wallet=wallet_id, cryptocurrency_id = cryptocurrency_id)

    # Update the balance
    wallet_balance.balance += Decimal(form.amount)
    wallet_balance.save()

    return {
        "success": True,
        "wallet_id": wallet_instance.id,
        "new_balance": float(wallet_balance.balance),
    }