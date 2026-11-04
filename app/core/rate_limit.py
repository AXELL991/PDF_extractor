"""Configuración del rate limiting por IP (slowapi)."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

settings = get_settings()

# Límite por defecto: 100/min por IP. Los endpoints sensibles lo endurecen.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="memory://" if settings.ENVIRONMENT == "development" else None,
)


def rate_limit_exceeded_handler(request, exc):
    """Handler público para rate limit excedido (reemplaza el privado de slowapi)."""
    from slowapi._rate_limit_exceeded_handler import (
        _rate_limit_exceeded_handler as _default_handler,
    )

    return _default_handler(request, exc)
