"""Compatibilidad: la lógica se dividió por responsabilidad.

La sanitización vive en ``sanitization.py`` y la validación de PDFs en
``pdf_validation.py``. Este módulo solo reexporta para no romper imports
históricos.
"""

from app.core.security.pdf_validation import PDF_MAGIC_NUMBERS, is_valid_pdf
from app.core.security.sanitization import sanitize_filename, sanitize_text

__all__ = [
    "PDF_MAGIC_NUMBERS",
    "is_valid_pdf",
    "sanitize_filename",
    "sanitize_text",
]
