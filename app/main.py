"""Composition root: instancia FastAPI, configura los middlewares de seguridad
y expone los endpoints definidos en `app.api.routes`.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes import build_router
from app.core.config import (
    ALLOWED_HOSTS,
    ALLOWED_ORIGINS,
    ENVIRONMENT,
    LOG_LEVEL,
    get_session_secret_key,
)
from app.core.exception_handlers import domain_exception_handler
from app.core.logging_config import setup_logging
from app.core.middleware import security_middleware
from app.core.rate_limit import limiter
from app.database import MongoRepository
from app.exceptions import DomainException
from app.services.pdf_extractor import PyPDFExtractor

setup_logging(log_level=LOG_LEVEL, environment=ENVIRONMENT)

# Fallar rápido si la configuración de producción está incompleta.
session_secret_key = get_session_secret_key()

db = MongoRepository()
extractor = PyPDFExtractor()


class AplicacionExtractor(FastAPI):
    """Aplicación FastAPI con el manejo uniforme de errores de dominio."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_exception_handler(DomainException, domain_exception_handler)


app = AplicacionExtractor(
    title="Extractor de PDF - UTN San Rafael",
    description="API segura para extracción de texto de PDFs con persistencia en MongoDB.",
    version="2.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    max_age=600,
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)
app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret_key,
    session_cookie="session_id",
    max_age=1800,
    same_site="lax",
    https_only=ENVIRONMENT == "production",
)
app.add_middleware(BaseHTTPMiddleware, dispatch=security_middleware)

# Dependencias publicadas para los proveedores de `app.api.dependencies`.
app.state.repositorio = db
app.state.extractor = extractor

app.include_router(build_router())
