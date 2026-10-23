"""Validación de archivos PDF reales."""

import io
import logging

from pypdf import PdfReader

logger = logging.getLogger("security")

# Magic numbers del formato PDF (%PDF- y %PDF).
PDF_MAGIC_NUMBERS = (
    b"%PDF-",
    b"\x25\x50\x44\x46",
)


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
