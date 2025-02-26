from ninja import Router
from django.http import HttpRequest
from typing import Dict, Any
from datetime import datetime

router = Router()

@router.get("/health")
def health_check(request: HttpRequest) -> Dict[str, Any]:
    """
    Simple health check endpoint to verify API is functioning.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.get("/ping")
def ping(request: HttpRequest) -> Dict[str, str]:
    """
    Simple ping endpoint for testing connectivity.
    """
    return {"message": "pong"}