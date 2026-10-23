"""Generación de identificadores opacos para trazabilidad HTTP."""

import secrets


def generate_request_id() -> str:
    """Genera un identificador criptográficamente seguro para una request."""
    return secrets.token_urlsafe(32)
