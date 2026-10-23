"""Middlewares HTTP: cabeceras de seguridad y logging."""

import logging
import time

from fastapi import Request

from app.core.security import generate_request_id

logger = logging.getLogger(__name__)

# Cabeceras de seguridad aplicadas a todas las respuestas
SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self';",
    "Permissions-Policy": "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
    "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}

# Swagger UI y ReDoc cargan scripts y estilos desde CDNs (jsdelivr) e inline.
DOCS_PATHS = {"/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}
DOCS_CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.jsdelivr.net; "
    "font-src 'self' https://cdn.jsdelivr.net;"
)


async def security_middleware(request: Request, call_next):
    """Aplica cabeceras de seguridad y loguea la request."""
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"

    logger.info(
        f"Request {request.method} {request.url.path} from {client_ip}",
        extra={
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", "unknown"),
            "request_path": request.url.path,
        },
    )

    response = await call_next(request)

    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    # Si es ruta de documentación interactiva, relajar CSP para permitir cargar Swagger UI de cdn.jsdelivr.net
    if request.url.path in DOCS_PATHS:
        response.headers["Content-Security-Policy"] = DOCS_CONTENT_SECURITY_POLICY

    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = generate_request_id()[:16]
    response.headers["X-Response-Time"] = str(round(process_time, 4))

    logger.info(
        f"Response {response.status_code} en {process_time:.4f}s",
        extra={
            "response_status": response.status_code,
            "client_ip": client_ip,
        },
    )

    return response
