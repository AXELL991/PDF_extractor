"""Manejador de excepciones que traduce errores de dominio a respuestas HTTP.

El dominio es puro (sin códigos HTTP); el mapeo a status codes vive aquí,
en la capa de presentación.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    ChecksumInvalidoError,
    DocumentoDuplicadoError,
    DocumentoInvalidoError,
    DocumentoNoEncontradoError,
    DomainException,
    ExtractionError,
    FormatoInvalidoError,
    NombreArchivoInvalidoError,
    TamañoExcedidoError,
)

logger = logging.getLogger(__name__)

# Mapeo de excepciones de dominio a códigos HTTP (capa de presentación).
EXCEPTION_STATUS_CODES = {
    DocumentoInvalidoError: 400,
    FormatoInvalidoError: 400,
    TamañoExcedidoError: 413,
    DocumentoDuplicadoError: 409,
    DocumentoNoEncontradoError: 404,
    ExtractionError: 422,
    ChecksumInvalidoError: 400,
    NombreArchivoInvalidoError: 400,
}


def _status_code_for(exc: DomainException) -> int:
    for exc_class, code in EXCEPTION_STATUS_CODES.items():
        if isinstance(exc, exc_class):
            return code
    return 400


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
        status_code=_status_code_for(exc),
        content={"detail": exc.message},
        headers={"X-Content-Type-Options": "nosniff"},
    )
