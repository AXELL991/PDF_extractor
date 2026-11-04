"""Proveedores de dependencias para el adaptador HTTP.

El composition root (`app.main`) publica el repositorio, el extractor, el
calculador de checksum y el servicio de seguridad en `app.state`. Los proveedores
construyen los casos de uso por request con esas dependencias, sin mutar
instancias compartidas.
"""

from fastapi import Depends, Request

from app.core.security.service import SecurityService
from app.domain.ports import DocumentRepositoryABC
from app.services.checksum import ChecksumCalculator
from app.services.pdf_extractor import PyPDFExtractor
from app.use_cases.gestionar_documentos import (
    ActualizarDocumentoUseCase,
    EliminarDocumentoUseCase,
    ListarDocumentosUseCase,
    ObtenerDocumentoUseCase,
)
from app.use_cases.procesar_documento import ProcesarDocumentoUseCase


def get_repositorio(request: Request) -> DocumentRepositoryABC:
    """Devuelve el repositorio configurado en el composition root."""
    repositorio = getattr(request.app.state, "repositorio", None)
    if repositorio is None:
        raise RuntimeError("El repositorio no está configurado en app.state.")
    return repositorio


def get_extractor(request: Request) -> PyPDFExtractor:
    """Devuelve el extractor configurado en el composition root."""
    extractor = getattr(request.app.state, "extractor", None)
    if extractor is None:
        raise RuntimeError("El extractor no está configurado en app.state.")
    return extractor


def get_checksum_calculator(request: Request) -> ChecksumCalculator:
    """Devuelve el calculador de checksum configurado en el composition root."""
    calculador = getattr(request.app.state, "checksum_calculator", None)
    if calculador is None:
        raise RuntimeError(
            "El calculador de checksum no está configurado en app.state."
        )
    return calculador


def get_sanitization(request: Request) -> SecurityService:
    """Devuelve el servicio de seguridad configurado en el composition root."""
    sanitization = getattr(request.app.state, "sanitization", None)
    if sanitization is None:
        raise RuntimeError("El servicio de seguridad no está configurado en app.state.")
    return sanitization


def get_max_size_bytes(request: Request) -> int:
    """Devuelve el límite máximo de tamaño en bytes configurado."""
    max_size = getattr(request.app.state, "max_size_bytes", None)
    if max_size is None:
        raise RuntimeError("El límite de tamaño no está configurado en app.state.")
    return max_size


def get_listar_documentos_use_case(
    repositorio: DocumentRepositoryABC = Depends(get_repositorio),
) -> ListarDocumentosUseCase:
    return ListarDocumentosUseCase(repositorio)


def get_obtener_documento_use_case(
    repositorio: DocumentRepositoryABC = Depends(get_repositorio),
    sanitization: SecurityService = Depends(get_sanitization),
) -> ObtenerDocumentoUseCase:
    return ObtenerDocumentoUseCase(repositorio, sanitization)


def get_actualizar_documento_use_case(
    repositorio: DocumentRepositoryABC = Depends(get_repositorio),
    sanitization: SecurityService = Depends(get_sanitization),
) -> ActualizarDocumentoUseCase:
    return ActualizarDocumentoUseCase(repositorio, sanitization)


def get_eliminar_documento_use_case(
    repositorio: DocumentRepositoryABC = Depends(get_repositorio),
    sanitization: SecurityService = Depends(get_sanitization),
) -> EliminarDocumentoUseCase:
    return EliminarDocumentoUseCase(repositorio, sanitization)


def get_procesar_documento_use_case(
    repositorio: DocumentRepositoryABC = Depends(get_repositorio),
    extractor: PyPDFExtractor = Depends(get_extractor),
    checksum_calculator: ChecksumCalculator = Depends(get_checksum_calculator),
    sanitization: SecurityService = Depends(get_sanitization),
    max_size_bytes: int = Depends(get_max_size_bytes),
) -> ProcesarDocumentoUseCase:
    return ProcesarDocumentoUseCase(
        extractor=extractor,
        db=repositorio,
        checksum_calculator=checksum_calculator,
        sanitization=sanitization,
        max_size_bytes=max_size_bytes,
    )
