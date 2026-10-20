"""Configuración del rate limiting por IP (slowapi)."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import ENVIRONMENT

# Límite por defecto: 100/min por IP. Los endpoints sensibles lo endurecen.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="memory://" if ENVIRONMENT == "development" else None,
)
