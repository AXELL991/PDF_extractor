"""Caso de uso para procesar y persistir documentos PDF.

Depende exclusivamente de puertos (Protocol) definidos en el dominio,
sin acoplamiento a implementaciones concretas de infraestructura.
"""

import io
from dataclasses import dataclass

from app.domain.entities import Documento
from app.domain.exceptions import (
    DocumentoDuplicadoError,
    FormatoInvalidoError,
    NombreArchivoInvalidoError,
    TamañoExcedidoError,
)
from app.domain.ports import (
    ChecksumCalculatorABC,
    DocumentRepositoryABC,
    PDFExtractorABC,
    SanitizationServiceABC,
)

# Valor de dominio para PDFs sin texto extraíble.
TEXTO_VACIO = "Vacio"


@dataclass(frozen=True)
class ResultadoDocumento:
    """Resultado de dominio del procesamiento de un PDF."""

    filename: str
    sha256: str


def validar_tamano_archivo(
    file_size: int | None,
    content_bytes: bytes | None,
    max_size_bytes: int,
) -> None:
    """Valida que el tamaño del archivo no exceda el límite permitido.

    Única regla centralizada de validación de tamaño.
    """
    size = file_size
    if size is None and content_bytes is not None:
        size = len(content_bytes)
    elif size is not None and content_bytes is not None:
        size = max(size, len(content_bytes))

    if (size or 0) > max_size_bytes:
        raise TamañoExcedidoError()


class ProcesarDocumentoUseCase:
    """Orquesta la validacion, extraccion y persistencia de un PDF."""

    def __init__(
        self,
        extractor: PDFExtractorABC,
        db: DocumentRepositoryABC,
        checksum_calculator: ChecksumCalculatorABC,
        sanitization: SanitizationServiceABC,
        max_size_bytes: int,
    ):
        self.extractor = extractor
        self.db = db
        self.checksum_calculator = checksum_calculator
        self.sanitization = sanitization
        self.max_size_bytes = max_size_bytes

    def execute(
        self,
        filename: str,
        content_bytes: bytes,
        file_size: int | None = None,
    ) -> ResultadoDocumento:
        """Valida el PDF, extrae su texto y lo guarda en la base de datos."""
        validar_tamano_archivo(file_size, content_bytes, self.max_size_bytes)
        nombre_sanitizado = self._sanitizar_nombre(filename)

        if not self.sanitization.validate_pdf(content_bytes):
            raise FormatoInvalidoError("El archivo no es un PDF válido.")

        checksum = self.checksum_calculator.calculate(content_bytes)
        self._verificar_duplicado(checksum)

        archivo_en_ram = io.BytesIO(content_bytes)
        texto_extraido = self.extractor.extract(archivo_en_ram)
        texto_seguro = self.sanitization.sanitize_text(texto_extraido)

        self.db.guardar_documento(
            Documento(
                archivo=nombre_sanitizado,
                texto=texto_seguro if texto_seguro else TEXTO_VACIO,
                hash_seguridad=checksum,
            )
        )

        return ResultadoDocumento(
            filename=nombre_sanitizado,
            sha256=checksum,
        )

    def _sanitizar_nombre(self, filename: str) -> str:
        """Sanitiza y valida que el nombre corresponda a un PDF."""
        try:
            return self.sanitization.sanitize_filename(filename)
        except ValueError as exc:
            raise NombreArchivoInvalidoError(str(exc)) from exc

    def _verificar_duplicado(self, checksum: str) -> None:
        """Verifica que el documento no exista ya en la base de datos."""
        if self.db.obtener_por_checksum(checksum) is not None:
            raise DocumentoDuplicadoError()
