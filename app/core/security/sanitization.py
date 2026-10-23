"""Sanitización de nombres de archivo y texto extraído."""

import os
import re

import bleach

# Patrón WHITELIST para nombres de archivo (alfanuméricos, guiones, puntos,
# guiones bajos y espacios).
FILENAME_PATTERN = re.compile(r"^[\w\-. ]+$")


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
