"""
extractor-pdf-utn - API REST segura para extracción de texto de PDFs.

Este módulo implementa una API FastAPI con múltiples capas de seguridad:
    - Logging estructurado y rotativo con formato JSON
    - Rate limiting por IP para prevenir DoS/Brute Force
    - CORS estricto con orígenes validados
    - Security Headers automáticos (HSTS, CSP, X-Frame-Options, etc.)
    - Validación de contenido de archivos por magic numbers y MIME type
    - Sanitización de inputs para prevenir inyecciones
    - Health checks con información limitada para evitar leaking
    - Monitoreo y métricas de seguridad

Versión: 2.0.0
"""

from __future__ import annotations

import contextlib
import io
import logging
import os
import time
from typing import Any

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.logging_config import setup_logging
from app.core.security import (
    generate_csrf_token,
    is_safe_ip,
    sanitize_filename,
    sanitize_text,
    validate_checksum,
    validate_file_content,
)
from app.database import MongoRepository
from app.dtos import ActualizarRequest, MensajeResponse, UploadResponse
from app.exceptions import DomainException
from app.services.pdf_extractor import PyPDFExtractor

# ============================================================
#  INICIALIZACIÓN DEL LOGGING SEGURO
# ============================================================
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
LOG_LEVEL = os.getenv("LOGLEVEL", "INFO")
setup_logging(log_level=LOG_LEVEL, environment=ENVIRONMENT)

logger = logging.getLogger(__name__)
logger.info(f"Iniciando aplicación en modo: {ENVIRONMENT}")

# ============================================================
#  CONFIGURACIÓN DE RATE LIMITING
# ============================================================
# Límite de requests: 100/min por IP para endpoints generales, 5/min para upload
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="memory://" if ENVIRONMENT == "development" else None,
)

# ============================================================
#  CONFIGURACIÓN DE CORS (Orígenes Validados)
# ============================================================
# Solo permitir orígenes explícitamente configurados
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8080,https://pdf-extractor.utn.edu.ar",
).split(",")

# ============================================================
#  CONSTANTES DE SEGURIDAD
# ============================================================
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
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

# ============================================================
#  INICIALIZACIÓN DE APLICACIÓN FASTAPI
# ============================================================
app = FastAPI(
    title="Extractor de PDF - UTN San Rafael",
    description="""
    API segura para extracción de texto de PDFs con persistencia en MongoDB.
    
    Características de seguridad:
    - Rate limiting por IP
    - Validación de archivos por magic numbers
    - Sanitización de inputs
    - Headers de seguridad HTTP
    - Logging estructurado y rotativo
    - CORS estricto
    """,
    version="2.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,
)

# ============================================================
#  INTEGRACIÓN DE RATE LIMITING
# ============================================================
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================================
#  MIDDLEWARES DE SEGURIDAD
# ============================================================

# 1. CORS estricto con orígenes validados
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    max_age=600,
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# 2. Trusted Host validation (evita Host header injection)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        ".utn.edu.ar",
        "pdf-extractor.utn.edu.ar",
        f"*.{os.getenv('HOST_SUFFIX', 'utn.edu.ar')}",
    ],
)

# 3. GZip compression con nivel seguro
app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)

# 4. Session middleware con clave segura
try:
    session_secret = os.getenv("SESSION_SECRET_KEY", os.urandom(32).hex())
    app.add_middleware(
        SessionMiddleware,
        secret_key=session_secret,
        session_cookie="session_id",
        max_age=1800,  # 30 minutos
        same_site="lax",
        https_only=ENVIRONMENT == "production",
    )
except Exception:
    logger.error("Error configurando SessionMiddleware", exc_info=True)


# ============================================================
#  MIDDLEWARE PARA INYECTAR SECURITY HEADERS Y LOGGING
# ============================================================
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """
    Middleware que aplica security headers, logging y rate limiting.
    """
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    # Logging del request entrante
    logger.info(
        f"Request {request.method} {request.url.path} from {client_ip}",
        extra={
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", "unknown"),
            "request_path": request.url.path,
        },
    )

    # Validar IP contra redes seguras (opcional, configurable vía env)
    if os.getenv("ENFORCE_IP_VALIDATION", "false").lower() == "true":
        if not is_safe_ip(client_ip):
            logger.warning(f"IP no autorizada: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Acceso denegado desde esta IP"},
            )

    response = await call_next(request)

    # Aplicar security headers a todas las respuestas
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    # Inyectar headers de rate limiting si están disponibles
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = generate_csrf_token()[:16]
    response.headers["X-Response-Time"] = str(round(process_time, 4))

    logger.info(
        f"Response {response.status_code} en {process_time:.4f}s",
        extra={
            "response_status": response.status_code,
            "client_ip": client_ip,
        },
    )

    return response


# ============================================================
#  INSTANCIAS DE SERVICIOS
# ============================================================
extractor = PyPDFExtractor()
db = MongoRepository()


# ============================================================
#  HANDLER DE EXCEPCIONES
# ============================================================
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
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


# ============================================================
#  ENDPOINTS
# ============================================================
@app.get(
    "/",
    tags=["Estado"],
    response_class=JSONResponse,
    summary="Endpoint de verificación de estado",
)
@limiter.limit("60/minute")
async def root(request: Request):
    """Endpoint de health check básico con información limitada."""
    return {
        "status": "online",
        "message": "API Extractor de PDF lista y conectada a MongoDB",
        "environment": ENVIRONMENT,
        "version": "2.0.0",
    }


@app.get(
    "/health",
    tags=["Estado"],
    response_class=JSONResponse,
    summary="Health check con métricas de sistema",
)
@limiter.limit("30/minute")
async def health_check(request: Request):
    """
    Endpoint de health check que devuelve estado del sistema
    sin exponer información sensible.
    """
    health_status = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "2.0.0",
        "environment": ENVIRONMENT,
    }
    
    # Verificar conexión a MongoDB
    try:
        db.client.admin.command("ping")
        health_status["database"] = "connected"
    except Exception as e:
        logger.error(f"Error de conexión a MongoDB: {e}")
        health_status["database"] = "disconnected"
        return JSONResponse(status_code=503, content=health_status)
    
    return health_status


@app.get(
    "/security.txt",
    tags=["Seguridad"],
    response_class=PlainTextResponse,
    summary="Información de contacto de seguridad",
)
async def security_txt():
    """Endpoint security.txt según RFC 9116."""
    return PlainTextResponse(
        "Contact: mailto:security@utn.edu.ar\n"
        "Expires: 2027-06-01T00:00:00Z\n"
        "Acknowledgments: https://utn.edu.ar/security/hall-of-fame\n"
        "Preferred-Languages: es, en\n"
        "Policy: https://utn.edu.ar/security/policy\n",
        media_type="text/plain",
    )


# =====================================================================
# C - CREATE (Subir y Procesar PDF)
# =====================================================================
@app.post(
    "/upload",
    tags=["Documentos (CRUD)"],
    summary="1. Crear: Subir PDF y guardar",
    response_model=UploadResponse,
)
@limiter.limit("5/minute")
async def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
    """
    Recibe un PDF, valida seguridad (formato, tamaño, magic numbers),
    verifica duplicado, extrae texto y lo guarda en MongoDB.
    """
    logger.info(f"Iniciando upload de archivo: {file.filename}")

    # --- Validación de tamaño antes de leer contenido ---
    if file.size and file.size > MAX_FILE_SIZE_BYTES:
        logger.warning(f"Archivo excede tamaño máximo: {file.size} bytes")
        from app.exceptions import TamañoExcedidoError
        raise TamañoExcedidoError(MAX_FILE_SIZE_MB)

    # --- Validación del nombre de archivo ---
    try:
        sanitized_name = sanitize_filename(file.filename or "")
    except ValueError as e:
        logger.warning(f"Nombre de archivo inválido: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # --- Leer contenido completo para validación profunda ---
    try:
        contents = await file.read()
    except Exception as e:
        logger.error(f"Error leyendo archivo: {e}")
        raise HTTPException(status_code=400, detail="Error leyendo el archivo.")

    if len(contents) > MAX_FILE_SIZE_BYTES:
        logger.warning(f"Archivo excede tamaño máximo tras lectura: {len(contents)} bytes")
        from app.exceptions import TamañoExcedidoError
        raise TamañoExcedidoError(MAX_FILE_SIZE_MB)

    # --- Validación por magic numbers y MIME type ---
    if not validate_file_content(contents):
        logger.warning("Archivo no pasó validación de contenido (magic numbers/MIME)")
        raise HTTPException(status_code=400, detail="El archivo no es un PDF válido.")

    # --- Procesamiento seguro en RAM ---
    archivo_en_ram = io.BytesIO(contents)
    try:
        checksum = extractor.calculate_checksum(archivo_en_ram)
        validate_checksum(checksum)  # Validar que sea un SHA-256 legítimo
        
        verificar_duplicado(checksum)

        texto_extraido = extractor.extract(archivo_en_ram)
        texto_sanitizado = sanitize_text(texto_extraido) if texto_extraido else "Vacio"

        db.guardar_documento(sanitized_name, texto_sanitizado, checksum)

        logger.info(f"PDF procesado y guardado: {sanitized_name} (sha256={checksum[:16]}...)")

        return UploadResponse(
            status="success",
            message="Documento procesado y guardado correctamente.",
            filename=sanitized_name,
            sha256=checksum,
        )
    finally:
        archivo_en_ram.close()


def validar_formato(filename: str):
    """Verifica que el archivo sea PDF (validación simple, extra)."""
    if not filename.lower().endswith(".pdf"):
        from app.exceptions import FormatoInvalidoError
        raise FormatoInvalidoError()


async def validar_tamaño(file: UploadFile):
    """Verifica que el archivo no exceda el tamaño máximo."""
    if file.size and file.size > MAX_FILE_SIZE_BYTES:
        from app.exceptions import TamañoExcedidoError
        raise TamañoExcedidoError(MAX_FILE_SIZE_MB)


def verificar_duplicado(checksum: str):
    """Verifica que el documento no exista ya en la base de datos."""
    if db.obtener_por_checksum(checksum):
        from app.exceptions import DocumentoDuplicadoError
        raise DocumentoDuplicadoError()


# =====================================================================
# R - READ (Leer documentos persistidos)
# =====================================================================
@app.get(
    "/documentos",
    tags=["Documentos (CRUD)"],
    summary="2. Leer: Listar todos los PDFs",
    response_class=JSONResponse,
)
@limiter.limit("60/minute")
async def listar_documentos(request: Request):
    """Devuelve una lista con todos los documentos procesados hasta ahora."""
    documentos = db.listar_todos()
    logger.info(f"Listados {len(documentos)} documentos")
    return {"total": len(documentos), "documentos": documentos}


@app.get(
    "/documentos/{checksum}",
    tags=["Documentos (CRUD)"],
    summary="2. Leer: Buscar por Hash",
    response_class=JSONResponse,
)
@limiter.limit("60/minute")
async def obtener_documento(checksum: str, request: Request):
    """Busca un documento específico utilizando su hash SHA-256."""
    try:
        validate_checksum(checksum)
    except ValueError as e:
        logger.warning(f"Checksum inválido recibido: {checksum}")
        raise HTTPException(status_code=400, detail=str(e))

    doc = db.obtener_por_checksum(checksum)
    if not doc:
        from app.exceptions import DocumentoNoEncontradoError
        raise DocumentoNoEncontradoError()

    doc.pop("_id", None)
    return doc


# =====================================================================
# U - UPDATE (Actualizar información)
# =====================================================================
@app.put(
    "/documentos/{checksum}",
    tags=["Documentos (CRUD)"],
    summary="3. Actualizar: Modificar nombre",
    response_model=MensajeResponse,
)
@limiter.limit("60/minute")
async def actualizar_documento(
    checksum: str, request: ActualizarRequest, fastapi_request: Request
):
    """Permite corregir el nombre de un archivo que ya fue guardado."""
    try:
        validate_checksum(checksum)
    except ValueError as e:
        logger.warning(f"Checksum inválido en PUT: {checksum}")
        raise HTTPException(status_code=400, detail=str(e))

    if not db.obtener_por_checksum(checksum):
        from app.exceptions import DocumentoNoEncontradoError
        raise DocumentoNoEncontradoError()

    # Sanitizar el nuevo nombre
    try:
        nuevo_nombre = sanitize_filename(request.nuevo_nombre)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.actualizar_nombre(checksum, nuevo_nombre)
    logger.info(f"Documento {checksum[:16]}... actualizado a: {nuevo_nombre}")

    return MensajeResponse(
        status="success",
        message=f"Nombre actualizado a: {nuevo_nombre}")


# =====================================================================
# D - DELETE (Borrar documento)
# =====================================================================
@app.delete(
    "/documentos/{checksum}",
    tags={"Documentos (CRUD)"},
    summary="4. Borrar: Eliminar PDF",
    response_model=MensajeResponse,
)
@limiter.limit("60/minute")
async def borrar_documento(checksum: str, request: Request):
    """Elimina permanentemente un registro de la base de datos."""
    try:
        validate_checksum(checksum)
    except ValueError as e:
        logger.warning(f"Checksum inválido en DELETE: {checksum}")
        raise HTTPException(status_code=400, detail=str(e))

    if not db.obtener_por_checksum(checksum):
        from app.exceptions import DocumentoNoEncontradoError
        raise DocumentoNoEncontradoError()

    db.eliminar_documento(checksum)
    logger.info(f"Documento {checksum[:16]}... eliminado")

    return MensajeResponse(
        status="success",
        message="Documento eliminado de la base de datos."
    )
