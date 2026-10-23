"""Endpoints HTTP de la API de extracción de PDFs.

Los handlers son finos: reciben la petición, delegan en un caso de uso
inyectado con `Depends()` y devuelven el DTO correspondiente.
"""

import logging
import time

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

from app.api.dependencies import (
    get_actualizar_documento_use_case,
    get_eliminar_documento_use_case,
    get_listar_documentos_use_case,
    get_obtener_documento_use_case,
    get_procesar_documento_use_case,
    get_repositorio,
)
from app.core.config import ENVIRONMENT
from app.core.rate_limit import limiter
from app.database import MongoRepository
from app.dtos import (
    ActualizarRequest,
    Documento,
    ListaDocumentosResponse,
    MensajeResponse,
    UploadResponse,
)
from app.use_cases.gestionar_documentos import (
    ActualizarDocumentoUseCase,
    EliminarDocumentoUseCase,
    ListarDocumentosUseCase,
    ObtenerDocumentoUseCase,
)
from app.use_cases.procesar_documento import ProcesarDocumentoUseCase

logger = logging.getLogger(__name__)


def build_router() -> APIRouter:
    """Construye el router con los endpoints de la API.

    Las dependencias se resuelven en cada request mediante `Depends()`, de
    modo que los tests pueden sustituir el repositorio o el extractor
    publicándolos en `app.state`.
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
    async def health_check(
        request: Request,
        repositorio: MongoRepository = Depends(get_repositorio),
    ):
        """Devuelve el estado del sistema sin exponer información sensible."""
        health_status = {
            "status": "healthy",
            "timestamp": int(time.time()),
            "version": "2.0.0",
            "environment": ENVIRONMENT,
        }

        try:
            repositorio.ping()
            health_status["database"] = "connected"
        except Exception as e:
            logger.error(f"Error de conexión a MongoDB: {e}")
            health_status["status"] = "unhealthy"
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
    async def upload_pdf(
        request: Request,
        file: UploadFile = File(...),
        use_case: ProcesarDocumentoUseCase = Depends(get_procesar_documento_use_case),
    ) -> UploadResponse:
        """Recibe un PDF y delega validación, extracción y persistencia."""
        logger.info(f"Iniciando upload de archivo: {file.filename}")
        contents = await file.read()
        return use_case.execute(
            filename=file.filename or "",
            content_bytes=contents,
            file_size=file.size,
        )

    @router.get(
        "/documentos",
        tags=["Documentos (CRUD)"],
        summary="2. Leer: Listar todos los PDFs",
        response_model=ListaDocumentosResponse,
    )
    @limiter.limit("60/minute")
    async def listar_documentos(
        request: Request,
        use_case: ListarDocumentosUseCase = Depends(get_listar_documentos_use_case),
    ) -> ListaDocumentosResponse:
        """Devuelve una lista con todos los documentos procesados hasta ahora."""
        documentos = use_case.execute()
        logger.info(f"Listados {len(documentos)} documentos")
        return ListaDocumentosResponse(total=len(documentos), documentos=documentos)

    @router.get(
        "/documentos/{checksum}",
        tags=["Documentos (CRUD)"],
        summary="2. Leer: Buscar por Hash",
        response_model=Documento,
    )
    @limiter.limit("60/minute")
    async def obtener_documento(
        checksum: str,
        request: Request,
        use_case: ObtenerDocumentoUseCase = Depends(get_obtener_documento_use_case),
    ) -> Documento:
        """Busca un documento específico utilizando su hash SHA-256."""
        return use_case.execute(checksum)

    @router.put(
        "/documentos/{checksum}",
        tags=["Documentos (CRUD)"],
        summary="3. Actualizar: Modificar nombre",
        response_model=MensajeResponse,
    )
    @limiter.limit("60/minute")
    async def actualizar_documento(
        checksum: str,
        request: Request,
        datos: ActualizarRequest,
        use_case: ActualizarDocumentoUseCase = Depends(get_actualizar_documento_use_case),
    ) -> MensajeResponse:
        """Permite corregir el nombre de un archivo que ya fue guardado."""
        nuevo_nombre = use_case.execute(checksum, datos.nuevo_nombre)
        logger.info(f"Documento {checksum[:16]}... actualizado a: {nuevo_nombre}")

        return MensajeResponse(
            status="success",
            message=f"Nombre actualizado a: {nuevo_nombre}",
        )

    @router.delete(
        "/documentos/{checksum}",
        tags={"Documentos (CRUD)"},
        summary="4. Borrar: Eliminar PDF",
        response_model=MensajeResponse,
    )
    @limiter.limit("60/minute")
    async def borrar_documento(
        checksum: str,
        request: Request,
        use_case: EliminarDocumentoUseCase = Depends(get_eliminar_documento_use_case),
    ) -> MensajeResponse:
        """Elimina permanentemente un registro de la base de datos."""
        use_case.execute(checksum)
        logger.info(f"Documento {checksum[:16]}... eliminado")

        return MensajeResponse(
            status="success",
            message="Documento eliminado de la base de datos.",
        )

    return router
