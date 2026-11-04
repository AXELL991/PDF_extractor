"""Utilidades de seguridad agrupadas por responsabilidad.

Este paquete mantiene una fachada compatible con los imports históricos de
``app.core.security`` mientras separa sanitización, validación de PDFs,
checksums y tokens en módulos cohesivos.
"""

from app.core.security.checksums import validate_checksum
from app.core.security.pdf_validation import is_valid_pdf
from app.core.security.sanitization import sanitize_filename, sanitize_text
from app.core.security.tokens import generate_request_id

__all__ = [
    "generate_request_id",
    "is_valid_pdf",
    "sanitize_filename",
    "sanitize_text",
    "validate_checksum",
]
