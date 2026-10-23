"""Composition root de la aplicación.

``create_app`` construye la app FastAPI e inyecta explícitamente sus
dependencias. La instancia ``app`` que usa Uvicorn se crea con los adaptadores
reales; los tests usan la misma factory con fakes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes import build_router
from app.core.config import (
    ALLOWED_HOSTS,
    ALLOWED_ORIGINS,
    ENVIRONMENT,
    LOG_LEVEL,
    validate_config,
)
from app.core.exception_handlers import domain_exception_handler
from app.core.logging_config import setup_logging
from app.core.middleware import security_middleware
from app.core.rate_limit import limiter
from app.database import MongoRepository
from app.exceptions import DomainException
from app.services.checksum import ChecksumCalculator
from app.services.pdf_extractor import PyPDFExtractor

setup_logging(log_level=LOG_LEVEL, environment=ENVIRONMENT)

# Fallar rápido si la configuración es inválida.
validate_config()


class AplicacionExtractor(FastAPI):
    """Aplicación FastAPI con el manejo uniforme de errores de dominio."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_exception_handler(DomainException, domain_exception_handler)


def create_app(
    repositorio: MongoRepository | None = None,
    extractor: PyPDFExtractor | None = None,
) -> FastAPI:
    """Construye la aplicación e inyecta sus dependencias.

    Args:
        repositorio: Adaptador de persistencia. Si es ``None`` se usa
            ``MongoRepository``.
        extractor: Adaptador de extracción. Si es ``None`` se usa
            ``PyPDFExtractor``.
    """
    aplicacion = AplicacionExtractor(
        title="Extractor de PDF - UTN San Rafael",
        description=(
            "API segura para extracción de texto de PDFs con persistencia en MongoDB."
        ),
        version="2.0.0",
        docs_url="/docs" if ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if ENVIRONMENT == "development" else None,
    )

    aplicacion.state.limiter = limiter
    aplicacion.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    aplicacion.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        max_age=600,
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )
    aplicacion.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
    aplicacion.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)
    aplicacion.add_middleware(BaseHTTPMiddleware, dispatch=security_middleware)

    # Dependencias publicadas para los proveedores de `app.api.dependencies`.
    aplicacion.state.repositorio = (
        repositorio if repositorio is not None else MongoRepository()
    )
    aplicacion.state.extractor = (
        extractor if extractor is not None else PyPDFExtractor()
    )
    aplicacion.state.checksum_calculator = ChecksumCalculator()

    aplicacion.include_router(build_router())
    return aplicacion


app = create_app()
