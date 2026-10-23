"""Caso de uso para procesar y persistir documentos PDF."""

import io

from app.core.config import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
from app.core.security import is_valid_pdf, sanitize_filename, sanitize_text
from app.database import MongoRepository
from app.dtos import Documento, UploadResponse
from app.exceptions import (
    DocumentoDuplicadoError,
    FormatoInvalidoError,
    NombreArchivoInvalidoError,
    TamañoExcedidoError,
)
from app.services.pdf_extractor import PyPDFExtractor

# Valor de dominio para PDFs sin texto extraíble. Se mantiene el literal
# histórico para no cambiar el contrato de la API.
TEXTO_VACIO = "Vacio"


def validar_tamano_archivo(file_size: int | None, content_bytes: bytes | None = None) -> None:
    """Valida que el tamaño del archivo no exceda el límite permitido.

    Única regla centralizada de validación de tamaño.
    """
    size = file_size
    if size is None and content_bytes is not None:
        size = len(content_bytes)
    elif size is not None and content_bytes is not None:
        size = max(size, len(content_bytes))

    if (size or 0) > MAX_FILE_SIZE_BYTES:
        raise TamañoExcedidoError(MAX_FILE_SIZE_MB)


class ProcesarDocumentoUseCase:
    """Orquesta la validacion, extraccion y persistencia de un PDF."""

    def __init__(self, extractor: PyPDFExtractor, db: MongoRepository):
        self.extractor = extractor
        self.db = db

    def execute(
        self,
        filename: str,
        content_bytes: bytes,
        file_size: int | None = None,
    ) -> UploadResponse:
        """Valida el PDF, extrae su texto y lo guarda en la base de datos."""
        validar_tamano_archivo(file_size, content_bytes)
        nombre_sanitizado = self._sanitizar_nombre(filename)

        if not is_valid_pdf(content_bytes):
            raise FormatoInvalidoError("El archivo no es un PDF válido.")

        archivo_en_ram = io.BytesIO(content_bytes)
        checksum = self.extractor.calculate_checksum(archivo_en_ram)
        self._verificar_duplicado(checksum)

        archivo_en_ram.seek(0)
        texto_extraido = self.extractor.extract(archivo_en_ram)
        texto_seguro = sanitize_text(texto_extraido)

        self.db.guardar_documento(
            Documento(
                archivo=nombre_sanitizado,
                texto=texto_seguro if texto_seguro else TEXTO_VACIO,
                hash_seguridad=checksum,
            )
        )

        return UploadResponse(
            status="success",
            message="Documento procesado y guardado correctamente.",
            filename=nombre_sanitizado,
            sha256=checksum,
        )

    def _sanitizar_nombre(self, filename: str) -> str:
        """Sanitiza y valida que el nombre corresponda a un PDF."""
        try:
            return sanitize_filename(filename)
        except ValueError as exc:
            raise NombreArchivoInvalidoError(str(exc)) from exc

    def _verificar_duplicado(self, checksum: str) -> None:
        """Verifica que el documento no exista ya en la base de datos."""
        if self.db.obtener_por_checksum(checksum) is not None:
            raise DocumentoDuplicadoError()
