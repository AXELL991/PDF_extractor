"""Validación de checksums SHA-256."""

import re


def validate_checksum(checksum: str) -> None:
    """Valida que el checksum sea un SHA-256 válido de 64 caracteres hexadecimales."""
    if not isinstance(checksum, str):
        raise ValueError("El checksum debe ser una cadena de texto.")
    if len(checksum) != 64:
        raise ValueError("El checksum debe tener exactamente 64 caracteres.")
    if not re.match(r"^[a-f0-9]{64}$", checksum, re.IGNORECASE):
        raise ValueError("El checksum debe ser un hash SHA-256 válido.")
