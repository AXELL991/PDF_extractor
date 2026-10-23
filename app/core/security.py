"""
Módulo de seguridad centralizado para el Extractor de PDF.
Contiene funciones de hardening, validación de archivos,
sanitización de inputs y validación de checksums.
"""

import io
import ipaddress
import logging
import os
import re
import secrets
from typing import Optional

import bleach
from pypdf import PdfReader

# ---------------------------------------------------------------------------
#  Configuración del logger de seguridad
# ---------------------------------------------------------------------------
logger = logging.getLogger("security")
logger.setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
#  Constantes de seguridad
# ---------------------------------------------------------------------------
# Patrón WHITELIST para nombres de archivo (alphanumeric, guiones, puntos, guiones bajos)
FILENAME_PATTERN = re.compile(r"^[\w\-. ]+$")

# Magic numbers del formato PDF (%PDF- y %PDF)
PDF_MAGIC_NUMBERS = (
    b"%PDF-",
    b"\x25\x50\x44\x46",
)


# ---------------------------------------------------------------------------
#  Sanitización de inputs
# ---------------------------------------------------------------------------
def sanitize_filename(filename: str) -> str:
    """Sanitiza el nombre de archivo eliminando caracteres peligrosos y path traversal."""
    if not filename:
        raise ValueError("El nombre de archivo no puede estar vacío.")

    filename = os.path.basename(filename)  # Elimina path traversal
    filename = bleach.clean(filename, tags=[], strip=True)  # Elimina HTML/JS
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)  # Elimina control chars
    filename = filename.strip(". ")  # Elimina puntos/espacios al inicio/final

    if not FILENAME_PATTERN.match(filename) or not filename.lower().endswith(".pdf"):
        raise ValueError("Nombre de archivo inválido o no es un PDF.")

    return filename


def sanitize_text(text: str) -> str:
    """Elimina HTML/JS del texto extraído, preservando el texto plano y Markdown."""
    if not text:
        return ""
    return bleach.clean(text, tags=[], strip=True)


def validate_checksum(checksum: str) -> None:
    """Valida que el checksum sea un SHA-256 válido de 64 caracteres hexadecimales."""
    if not isinstance(checksum, str):
        raise ValueError("El checksum debe ser una cadena de texto.")
    if len(checksum) != 64:
        raise ValueError("El checksum debe tener exactamente 64 caracteres.")
    if not re.match(r"^[a-f0-9]{64}$", checksum, re.IGNORECASE):
        raise ValueError("El checksum debe ser un hash SHA-256 válido.")


def is_safe_ip(client_ip: str, allowed_networks: Optional[list] = None) -> bool:
    """
    Verifica si una IP de cliente está dentro de redes permitidas.
    Por defecto permite localhost y rangos privados.
    """
    if allowed_networks is None:
        allowed_networks = [
            "127.0.0.0/8",
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16",
            "::1/128",
            "fe80::/10",
        ]

    try:
        ip = ipaddress.ip_address(client_ip)
        for network in allowed_networks:
            if ip in ipaddress.ip_network(network):
                return True
    except ValueError:
        logger.warning(f"IP inválida detectada: {client_ip}")

    return False


# ---------------------------------------------------------------------------
#  Hardening de archivos
# ---------------------------------------------------------------------------
def is_valid_pdf(content: bytes) -> bool:
    """
    Verifica que el contenido sea un PDF real.

    Primero exige el magic number y luego intenta parsear el documento con
    pypdf. Un archivo que solo copia la cabecera ``%PDF-`` pero está corrupto
    no se considera válido.
    """
    if not content:
        logger.warning("Contenido de archivo vacío.")
        return False

    if not any(content.startswith(magic) for magic in PDF_MAGIC_NUMBERS):
        logger.warning("Magic number de PDF no detectado.")
        return False

    try:
        reader = PdfReader(io.BytesIO(content))
        # Forzar la lectura del árbol de páginas para detectar PDFs truncados.
        _ = len(reader.pages)
        return True
    except Exception as exc:
        logger.warning(f"PDF no parseable: {exc}")
        return False


# ---------------------------------------------------------------------------
#  Generación de tokens seguros
# ---------------------------------------------------------------------------
def generate_csrf_token() -> str:
    """Genera un token CSRF criptográficamente seguro."""
    return secrets.token_urlsafe(32)
