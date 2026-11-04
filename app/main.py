"""Composition root de la aplicación.

``create_app`` construye la app FastAPI e inyecta explícitamente sus
dependencias. La instancia ``app`` que usa Uvicorn se crea con los adaptadores
reales; los tests usan la misma factory con fakes.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes import build_router
from app.core.config import get_settings, validate_config
from app.core.logging_config import setup_logging
from app.core.middleware import security_middleware
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.security.service import SecurityService
from app.database import MongoDocumentRepository
from app.domain.exceptions import DomainException
from app.services.checksum import ChecksumCalculator
from app.services.pdf_extractor import PyPDFExtractor

settings = get_settings()
setup_logging(log_level=settings.LOG_LEVEL, environment=settings.ENVIRONMENT)

# Fallar rápido si la configuración es inválida.
validate_config()


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


class AplicacionExtractor(FastAPI):
    """Aplicación FastAPI con el manejo uniforme de errores de dominio."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_exception_handler(DomainException, domain_exception_handler)


def create_app(
    repositorio: MongoDocumentRepository | None = None,
    extractor: PyPDFExtractor | None = None,
    checksum_calculator: ChecksumCalculator | None = None,
) -> FastAPI:
    """Construye la aplicación e inyecta sus dependencias.

    Args:
        repositorio: Adaptador de persistencia. Si es ``None`` se usa
            ``MongoDocumentRepository``.
        extractor: Adaptador de extracción. Si es ``None`` se usa
            ``PyPDFExtractor``.
        checksum_calculator: Adaptador de checksum. Si es ``None`` se usa
            ``ChecksumCalculator``.
    """
    aplicacion = AplicacionExtractor(
        title="Extractor de PDF - UTN San Rafael",
        description=(
            "API segura para extracción de texto de PDFs con persistencia en MongoDB."
        ),
        version="2.0.0",
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    )

    aplicacion.state.limiter = limiter
    aplicacion.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    aplicacion.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        max_age=600,
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )
    aplicacion.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)
    aplicacion.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)
    aplicacion.add_middleware(BaseHTTPMiddleware, dispatch=security_middleware)

    # Dependencias publicadas para los proveedores de `app.api.dependencies`.
    aplicacion.state.repositorio = (
        repositorio if repositorio is not None else MongoDocumentRepository()
    )
    aplicacion.state.extractor = (
        extractor if extractor is not None else PyPDFExtractor()
    )
    aplicacion.state.checksum_calculator = (
        checksum_calculator if checksum_calculator is not None else ChecksumCalculator()
    )
    aplicacion.state.max_size_bytes = settings.MAX_FILE_SIZE_BYTES
    aplicacion.state.sanitization = SecurityService()

    aplicacion.include_router(build_router())
    return aplicacion


app = create_app()
