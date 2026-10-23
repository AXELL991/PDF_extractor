"""Casos de uso CRUD de documentos.

La capa de aplicación concentra las reglas de existencia, validación de
checksum y sanitización del nombre. Los adaptadores HTTP solo traducen la
petición y la respuesta.
"""

from app.core.security import sanitize_filename, validate_checksum
from app.database import MongoRepository
from app.domain.entities import Documento
from app.exceptions import (
    ChecksumInvalidoError,
    DocumentoNoEncontradoError,
    NombreArchivoInvalidoError,
)


def _obtener_documento(repositorio: MongoRepository, checksum: str) -> Documento:
    """Valida el checksum y devuelve el documento o lanza el error de dominio."""
    try:
        validate_checksum(checksum)
    except ValueError as exc:
        raise ChecksumInvalidoError(str(exc)) from exc

    documento = repositorio.obtener_por_checksum(checksum)
    if documento is None:
        raise DocumentoNoEncontradoError()
    return documento


class ListarDocumentosUseCase:
    """Devuelve todos los documentos persistidos."""

    def __init__(self, repositorio: MongoRepository):
        self.repositorio = repositorio

    def execute(self) -> list[Documento]:
        return self.repositorio.listar_todos()


class ObtenerDocumentoUseCase:
    """Obtiene un documento por su checksum."""

    def __init__(self, repositorio: MongoRepository):
        self.repositorio = repositorio

    def execute(self, checksum: str) -> Documento:
        return _obtener_documento(self.repositorio, checksum)


class ActualizarDocumentoUseCase:
    """Actualiza el nombre de un documento existente."""

    def __init__(self, repositorio: MongoRepository):
        self.repositorio = repositorio

    def execute(self, checksum: str, nuevo_nombre: str) -> str:
        _obtener_documento(self.repositorio, checksum)
        try:
            nombre_sanitizado = sanitize_filename(nuevo_nombre)
        except ValueError as exc:
            raise NombreArchivoInvalidoError(str(exc)) from exc

        self.repositorio.actualizar_nombre(checksum, nombre_sanitizado)
        return nombre_sanitizado


class EliminarDocumentoUseCase:
    """Elimina un documento existente."""

    def __init__(self, repositorio: MongoRepository):
        self.repositorio = repositorio

    def execute(self, checksum: str) -> None:
        _obtener_documento(self.repositorio, checksum)
        self.repositorio.eliminar_documento(checksum)
