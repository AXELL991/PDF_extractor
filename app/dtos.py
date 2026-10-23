"""Esquemas Pydantic de transferencia de la capa API."""

from pydantic import BaseModel, ConfigDict

from app.domain.entities import Documento as DocumentoDominio


class DocumentoResponse(BaseModel):
    """Representación HTTP de un documento persistido."""

    model_config = ConfigDict(from_attributes=True)

    archivo: str
    texto: str = ""
    hash_seguridad: str


class ListaDocumentosResponse(BaseModel):
    """DTO para listar todos los documentos."""

    total: int
    documentos: list[DocumentoResponse]


class UploadResponse(BaseModel):
    """DTO para respuesta de subida exitosa."""

    status: str
    message: str
    filename: str
    sha256: str


class MensajeResponse(BaseModel):
    """DTO para mensajes simples de exito."""

    status: str
    message: str


class ActualizarRequest(BaseModel):
    """DTO para request de actualizacion."""

    nuevo_nombre: str


# Alias de compatibilidad para consumidores que importaban la entidad desde
# este módulo. La entidad real ahora es un dataclass puro de dominio.
Documento = DocumentoDominio

__all__ = [
    "ActualizarRequest",
    "Documento",
    "DocumentoResponse",
    "ListaDocumentosResponse",
    "MensajeResponse",
    "UploadResponse",
]
