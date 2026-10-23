"""Manejadores de excepciones que traducen errores de dominio a respuestas HTTP."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions import DomainException

logger = logging.getLogger(__name__)


async def domain_exception_handler(
    request: Request, exc: DomainException
) -> JSONResponse:
    """Maneja todas las excepciones del dominio de forma uniforme y segura."""
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        f"Excepción de dominio: {exc.message} (IP: {client_ip})",
        extra={"client_ip": client_ip, "exception": exc},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
        headers={"X-Content-Type-Options": "nosniff"},
    )
