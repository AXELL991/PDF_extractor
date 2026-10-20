"""Caso de uso para procesar y persistir documentos PDF."""
import io

from app.database import MongoRepository
from app.dtos import UploadResponse
from app.exceptions import (
    DocumentoDuplicadoError,
    FormatoInvalidoError,
    TamañoExcedidoError,
)
from app.services.pdf_extractor import PyPDFExtractor

MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


class ProcesarDocumentoUseCase:
    """Orquesta la validacion, extraccion y persistencia de un PDF."""

    def __init__(self, extractor: PyPDFExtractor, db: MongoRepository):
        self.extractor = extractor
        self.db = db

    def execute(
        self,
        filename: str,
        content_bytes: bytes,
        file_size: int | None,
    ) -> UploadResponse:
        """Valida el PDF, extrae su texto y lo guarda en la base de datos."""
        self._validar_formato(filename)
        self._validar_tamaño(file_size, content_bytes)

        archivo_en_ram = io.BytesIO(content_bytes)
        checksum = self.extractor.calculate_checksum(archivo_en_ram)
        self._verificar_duplicado(checksum)

        archivo_en_ram.seek(0)
        texto_extraido = self.extractor.extract(archivo_en_ram)

        self.db.guardar_documento(
            filename,
            texto_extraido if texto_extraido else "Vacio",
            checksum,
        )

        return UploadResponse(
            status="success",
            message="Documento procesado y guardado correctamente.",
            filename=filename,
            sha256=checksum,
        )

    def _validar_formato(self, filename: str) -> None:
        """Verifica que el archivo sea PDF."""
        if not filename or not filename.lower().endswith(".pdf"):
            raise FormatoInvalidoError()

    def _validar_tamaño(self, file_size: int | None, content_bytes: bytes) -> None:
        """Verifica que el archivo no exceda el tamaño maximo."""
        size = max(file_size or 0, len(content_bytes))
        if size > MAX_FILE_SIZE_BYTES:
            raise TamañoExcedidoError(MAX_FILE_SIZE_MB)

    def _verificar_duplicado(self, checksum: str) -> None:
        """Verifica que el documento no exista ya en la base de datos."""
        if self.db.obtener_por_checksum(checksum):
            raise DocumentoDuplicadoError()
