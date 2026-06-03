"""
Módulo de seguridad centralizado para el Extractor de PDF.
Contiene funciones de hardening, validación de archivos,
sanitización de inputs, hashing seguro y generación de CSRF tokens.
"""

import hashlib
import hmac
import ipaddress
import logging
import os
import re
import secrets
from typing import Optional

import bleach
from argon2 import PasswordHasher

# ---------------------------------------------------------------------------
#  Configuración del logger de seguridad
# ---------------------------------------------------------------------------
logger = logging.getLogger("security")
logger.setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
#  Constantes de seguridad
# ---------------------------------------------------------------------------
MAX_CONTENT_LENGTH_MB = 5
MAX_FILE_SIZE_BYTES = MAX_CONTENT_LENGTH_MB * 1024 * 1024
ALLOWED_MIMETYPES = {"application/pdf"}
PDF_MAGIC_NUMBERS = (
    b"%PDF-",
    b"\x25\x50\x44\x46",
)
# Patrón WHITELIST para nombres de archivo (alphanumeric, guiones, puntos, guiones bajos)
FILENAME_PATTERN = re.compile(r"^[\w\-. ]+$")

# ---------------------------------------------------------------------------
#  Hasher de contraseñas con Argon2id
# ---------------------------------------------------------------------------
ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=1, hash_len=32)


def hash_password(password: str) -> str:
    """Genera un hash Argon2id seguro para la contraseña dada."""
    return ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash Argon2id."""
    try:
        ph.verify(hashed, password)
        return True
    except Exception:
        return False


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
    Verifica que el contenido sea un PDF válido usando magic numbers.
    
    chequea que comience con %PDF- o con el magic number binario de PDF.
    """
    if not content:
        logger.warning("Contenido de archivo vacío.")
        return False

    for magic in PDF_MAGIC_NUMBERS:
        if content.startswith(magic):
            return True

    logger.warning("Magic number de PDF no detectado.")
    return False


def verify_mime_type(content: bytes) -> str:
    """
    Detecta el tipo MIME real del contenido usando python-magic.
    """
    import magic
    
    detected = magic.from_buffer(content, mime=True)
    logger.debug(f"Tipo MIME detectado: {detected}")
    return detected


def validate_file_content(content: bytes) -> bool:
    """
    Verificación completa del contenido del archivo:
      1. Magic number PDF
      2. Tipo MIME correcto
      3. Tamaño dentro de límites
    """
    if len(content) > MAX_FILE_SIZE_BYTES:
        logger.warning(f"Archivo excede tamaño máximo: {len(content)} bytes")
        return False

    if not is_valid_pdf(content):
        logger.warning("Archivo no parece ser un PDF válido (magic number check fallido)")
        return False

    try:
        detected_type = verify_mime_type(content)
        if detected_type not in ALLOWED_MIMETYPES:
            logger.warning(f"Tipo MIME inesperado: {detected_type}")
            return False
    except Exception as e:
        logger.error(f"Error validando MIME type: {e}")
        return False

    return True


# ---------------------------------------------------------------------------
# Generación HMAC seguro
# ---------------------------------------------------------------------------
def generate_hmac(message: str, secret: str) -> str:
    """Genera un HMAC-SHA256 para un mensaje dado."""
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# CSRF Token simple pero seguro
# ---------------------------------------------------------------------------
def generate_csrf_token() -> str:
    """Genera un token CSRF criptográficamente seguro."""
    return secrets.token_urlsafe(32)


# ---------------------------------------------------------------------------
# Sanitización de texto extraído del PDF para prevenir XSS
# ---------------------------------------------------------------------------
def sanitize_text(text: str) -> str:
    """
    Sanitiza el texto extraído del PDF para prevenir inyección de HTML/JS.
    """
    return bleach.clean(text, tags=[], strip=True)
