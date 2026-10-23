"""Cálculo de checksums SHA-256 para contenido binario."""

import hashlib


class ChecksumCalculator:
    """Calcula el hash SHA-256 de un contenido en memoria."""

    def calculate(self, content: bytes) -> str:
        """Devuelve el SHA-256 hexadecimal del contenido recibido."""
        return hashlib.sha256(content).hexdigest()
