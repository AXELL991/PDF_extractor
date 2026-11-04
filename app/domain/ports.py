"""Contratos (puertos) de salida del dominio.

Define las abstracciones que la capa de aplicación requiere para
persistir, extraer, calcular checksums y sanitizar, sin acoplarse a
implementaciones concretas de infraestructura.
"""

from typing import Protocol

from app.domain.entities import Documento


class DocumentRepositoryABC(Protocol):
    """Contrato de persistencia para documentos."""

    def obtener_por_checksum(self, checksum: str) -> Documento | None: ...
    def guardar_documento(self, documento: Documento) -> None: ...
    def listar_todos(self) -> list[Documento]: ...
    def actualizar_nombre(self, checksum: str, nuevo_nombre: str) -> None: ...
    def eliminar_documento(self, checksum: str) -> None: ...
    def ping(self) -> None: ...


class PDFExtractorABC(Protocol):
    """Contrato de extracción de texto desde un PDF."""

    def extract(self, file_stream) -> str: ...


class ChecksumCalculatorABC(Protocol):
    """Contrato de cálculo de checksum SHA-256."""

    def calculate(self, content: bytes) -> str: ...


class SanitizationServiceABC(Protocol):
    """Contrato de sanitización de nombres de archivo y texto."""

    def sanitize_filename(self, filename: str) -> str: ...
    def sanitize_text(self, text: str) -> str: ...
    def validate_pdf(self, content: bytes) -> bool: ...
    def validate_checksum(self, checksum: str) -> None: ...
