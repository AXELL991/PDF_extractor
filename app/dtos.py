from pydantic import BaseModel
from typing import List, Optional


class DocumentoResponse(BaseModel):
    """DTO para respuestas de documentos individuales."""
    archivo: str
    texto: str
    hash_seguridad: str


class ListaDocumentosResponse(BaseModel):
    """DTO para listar todos los documentos."""
    total: int
    documentos: List[dict]


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
