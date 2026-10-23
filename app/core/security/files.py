"""Sanitización de nombres/textos y validación de archivos PDF."""

import io
import logging
import os
import re

import bleach
from pypdf import PdfReader

logger = logging.getLogger("security")

# Patrón WHITELIST para nombres de archivo (alfanuméricos, guiones, puntos,
# guiones bajos y espacios).
FILENAME_PATTERN = re.compile(r"^[\w\-. ]+$")

# Magic numbers del formato PDF (%PDF- y %PDF).
PDF_MAGIC_NUMBERS = (
    b"%PDF-",
    b"\x25\x50\x44\x46",
)


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


def is_valid_pdf(content: bytes) -> bool:
    """Verifica que el contenido sea un PDF real y parseable.

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
