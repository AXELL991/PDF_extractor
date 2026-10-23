"""Proveedores de dependencias para el adaptador HTTP.

El composition root (`app.main`) publica el repositorio, el extractor y el
calculador de checksum en `app.state`. Los proveedores construyen los casos de
uso por request con esas dependencias, sin mutar instancias compartidas.
"""

from fastapi import Depends, Request

from app.database import MongoRepository
from app.services.checksum import ChecksumCalculator
from app.services.pdf_extractor import PyPDFExtractor
from app.use_cases.gestionar_documentos import (
    ActualizarDocumentoUseCase,
    EliminarDocumentoUseCase,
    ListarDocumentosUseCase,
    ObtenerDocumentoUseCase,
)
from app.use_cases.procesar_documento import ProcesarDocumentoUseCase


def get_repositorio(request: Request) -> MongoRepository:
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


def get_listar_documentos_use_case(
    repositorio: MongoRepository = Depends(get_repositorio),
) -> ListarDocumentosUseCase:
    return ListarDocumentosUseCase(repositorio)


def get_obtener_documento_use_case(
    repositorio: MongoRepository = Depends(get_repositorio),
) -> ObtenerDocumentoUseCase:
    return ObtenerDocumentoUseCase(repositorio)


def get_actualizar_documento_use_case(
    repositorio: MongoRepository = Depends(get_repositorio),
) -> ActualizarDocumentoUseCase:
    return ActualizarDocumentoUseCase(repositorio)


def get_eliminar_documento_use_case(
    repositorio: MongoRepository = Depends(get_repositorio),
) -> EliminarDocumentoUseCase:
    return EliminarDocumentoUseCase(repositorio)


def get_procesar_documento_use_case(
    repositorio: MongoRepository = Depends(get_repositorio),
    extractor: PyPDFExtractor = Depends(get_extractor),
    checksum_calculator: ChecksumCalculator = Depends(get_checksum_calculator),
) -> ProcesarDocumentoUseCase:
    return ProcesarDocumentoUseCase(
        extractor=extractor,
        db=repositorio,
        checksum_calculator=checksum_calculator,
    )
