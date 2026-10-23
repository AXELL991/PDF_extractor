"""Utilidades de seguridad agrupadas por responsabilidad.

Este paquete mantiene una fachada compatible con los imports históricos de
``app.core.security`` mientras separa sanitización, checksums y tokens en
módulos cohesivos.
"""

from app.core.security.checksums import validate_checksum
from app.core.security.files import (
    PDF_MAGIC_NUMBERS,
    sanitize_filename,
    sanitize_text,
    is_valid_pdf,
)
from app.core.security.tokens import generate_request_id

__all__ = [
    "PDF_MAGIC_NUMBERS",
    "generate_request_id",
    "is_valid_pdf",
    "sanitize_filename",
    "sanitize_text",
    "validate_checksum",
]
