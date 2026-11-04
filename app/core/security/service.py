"""Adaptador de seguridad que implementa el puerto SanitizationServiceABC."""

from app.core.security.checksums import validate_checksum as _validate_checksum
from app.core.security.pdf_validation import is_valid_pdf as _is_valid_pdf
from app.core.security.sanitization import (
    sanitize_filename as _sanitize_filename,
    sanitize_text as _sanitize_text,
)
from app.domain.ports import SanitizationServiceABC


class SecurityService(SanitizationServiceABC):
    """Implementación concreta de sanitización y validación de seguridad."""

    def sanitize_filename(self, filename: str) -> str:
        return _sanitize_filename(filename)

    def sanitize_text(self, text: str) -> str:
        return _sanitize_text(text)

    def validate_pdf(self, content: bytes) -> bool:
        return _is_valid_pdf(content)

    def validate_checksum(self, checksum: str) -> None:
        _validate_checksum(checksum)
