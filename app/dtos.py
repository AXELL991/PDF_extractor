from pydantic import BaseModel
from typing import List


class Documento(BaseModel):
    """Entidad/DTO de un documento persistido."""
    archivo: str
    texto: str = ""
    hash_seguridad: str


class ListaDocumentosResponse(BaseModel):
    """DTO para listar todos los documentos."""
    total: int
    documentos: List[Documento]


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
