"""Endpoints HTTP de la API de extracción de PDFs.

Los handlers son finos: validan la entrada HTTP y delegan el trabajo en el
caso de uso `ProcesarDocumentoUseCase` o en el repositorio.
"""

import logging
import time

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

from app.core.config import ENVIRONMENT
from app.core.rate_limit import limiter
from app.core.security import is_valid_pdf, sanitize_filename, validate_checksum
from app.dtos import ActualizarRequest, MensajeResponse, UploadResponse
from app.exceptions import DocumentoNoEncontradoError, TamañoExcedidoError
from app.use_cases.procesar_documento import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB

logger = logging.getLogger(__name__)


def build_router(get_db, use_case) -> APIRouter:
    """Construye el router con los endpoints de la API.

    `get_db` resuelve el repositorio activo en cada request, de modo que la
    capa de composición pueda inyectar un doble en los tests. `use_case` es el
    caso de uso `ProcesarDocumentoUseCase`.
    """
    router = APIRouter()

    @router.get(
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

    @router.get(
        "/health",
        tags=["Estado"],
        response_class=JSONResponse,
        summary="Health check con métricas de sistema",
    )
    @limiter.limit("30/minute")
    async def health_check(request: Request):
        """Devuelve el estado del sistema sin exponer información sensible."""
        health_status = {
            "status": "healthy",
            "timestamp": int(time.time()),
            "version": "2.0.0",
            "environment": ENVIRONMENT,
        }

        try:
            get_db().client.admin.command("ping")
            health_status["database"] = "connected"
        except Exception as e:
            logger.error(f"Error de conexión a MongoDB: {e}")
            health_status["database"] = "disconnected"
            return JSONResponse(status_code=503, content=health_status)

        return health_status

    @router.get(
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

    @router.post(
        "/upload",
        tags=["Documentos (CRUD)"],
        summary="1. Crear: Subir PDF y guardar",
        response_model=UploadResponse,
    )
    @limiter.limit("5/minute")
    async def upload_pdf(request: Request, file: UploadFile = File(...)) -> UploadResponse:
        """Recibe un PDF, valida seguridad (nombre, tamaño, magic numbers),
        verifica duplicado, extrae texto y lo guarda en MongoDB.
        """
        logger.info(f"Iniciando upload de archivo: {file.filename}")

        # --- Validación de tamaño antes de leer el contenido ---
        if file.size and file.size > MAX_FILE_SIZE_BYTES:
            logger.warning(f"Archivo excede tamaño máximo: {file.size} bytes")
            raise TamañoExcedidoError(MAX_FILE_SIZE_MB)

        # --- Validación y sanitización del nombre de archivo ---
        try:
            sanitized_name = sanitize_filename(file.filename or "")
        except ValueError as e:
            logger.warning(f"Nombre de archivo inválido: {e}")
            raise HTTPException(status_code=400, detail=str(e))

        contents = await file.read()

        # --- Validación por magic numbers (contenido realmente PDF) ---
        if not is_valid_pdf(contents):
            logger.warning("El contenido no tiene la firma magic de un PDF")
            raise HTTPException(status_code=400, detail="El archivo no es un PDF válido.")

        # --- Lógica de negocio: checksum, duplicados, extracción y persistencia ---
        # Se re-liga el repositorio del módulo para mantenerlo intercambiable (tests).
        use_case.db = get_db()
        return use_case.execute(
            filename=sanitized_name,
            content_bytes=contents,
            file_size=file.size,
        )

    @router.get(
        "/documentos",
        tags=["Documentos (CRUD)"],
        summary="2. Leer: Listar todos los PDFs",
        response_class=JSONResponse,
    )
    @limiter.limit("60/minute")
    async def listar_documentos(request: Request):
        """Devuelve una lista con todos los documentos procesados hasta ahora."""
        documentos = get_db().listar_todos()
        logger.info(f"Listados {len(documentos)} documentos")
        return {"total": len(documentos), "documentos": documentos}

    @router.get(
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

        doc = get_db().obtener_por_checksum(checksum)
        if not doc:
            raise DocumentoNoEncontradoError()

        doc.pop("_id", None)
        return doc

    @router.put(
        "/documentos/{checksum}",
        tags=["Documentos (CRUD)"],
        summary="3. Actualizar: Modificar nombre",
        response_model=MensajeResponse,
    )
    @limiter.limit("60/minute")
    async def actualizar_documento(
        checksum: str, request: Request, datos: ActualizarRequest
    ):
        """Permite corregir el nombre de un archivo que ya fue guardado."""
        try:
            validate_checksum(checksum)
        except ValueError as e:
            logger.warning(f"Checksum inválido en PUT: {checksum}")
            raise HTTPException(status_code=400, detail=str(e))

        if not get_db().obtener_por_checksum(checksum):
            raise DocumentoNoEncontradoError()

        # Sanitizar el nuevo nombre
        try:
            nuevo_nombre = sanitize_filename(datos.nuevo_nombre)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        get_db().actualizar_nombre(checksum, nuevo_nombre)
        logger.info(f"Documento {checksum[:16]}... actualizado a: {nuevo_nombre}")

        return MensajeResponse(
            status="success",
            message=f"Nombre actualizado a: {nuevo_nombre}")

    @router.delete(
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

        if not get_db().obtener_por_checksum(checksum):
            raise DocumentoNoEncontradoError()

        get_db().eliminar_documento(checksum)
        logger.info(f"Documento {checksum[:16]}... eliminado")

        return MensajeResponse(
            status="success",
            message="Documento eliminado de la base de datos."
        )

    return router
