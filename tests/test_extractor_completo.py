"""Tests completos para el extractor de PDF a Markdown."""

import io

import pytest

from app.exceptions import ExtractionError
from app.services.checksum import ChecksumCalculator
from app.services.pdf_extractor import PyPDFExtractor


def test_extract_text_from_pdf(pdf_con_texto):
    """Verifica que el extractor devuelva el texto real de un PDF válido."""
    extractor = PyPDFExtractor()
    resultado = extractor.extract(io.BytesIO(pdf_con_texto))

    assert "Hola PDF de prueba" in resultado
    assert "## Página 1" in resultado


def test_extract_lanza_error_ante_fallo_de_lectura(monkeypatch):
    """Un fallo de pypdf debe convertirse en un error de dominio explícito."""

    class LectorRoto:
        def __init__(self, *args, **kwargs):
            raise ValueError("PDF ilegible")

    monkeypatch.setattr("app.services.pdf_extractor.PdfReader", LectorRoto)
    extractor = PyPDFExtractor()

    with pytest.raises(ExtractionError):
        extractor.extract(io.BytesIO(b"%PDF-1.4"))


def test_extract_pdf_sin_texto_devuelve_vacio(monkeypatch):
    """Si la lectura funciona pero no hay texto, el extractor devuelve una cadena vacía."""

    class PaginaVacia:
        def extract_text(self):
            return ""

    class LectorVacio:
        def __init__(self, *args, **kwargs):
            self.pages = [PaginaVacia()]

    monkeypatch.setattr("app.services.pdf_extractor.PdfReader", LectorVacio)
    extractor = PyPDFExtractor()

    assert extractor.extract(io.BytesIO(b"%PDF-1.4")) == ""


def test_format_page_to_markdown():
    """Verifica la conversion estructurada a Markdown."""
    extractor = PyPDFExtractor()
    texto_ejemplo = (
        "TITULO PRINCIPAL:\n- Elemento 1\n- Elemento 2\nTexto normal del parrafo."
    )
    markdown = extractor._format_page_to_markdown(texto_ejemplo, 1)

    assert "## Página 1" in markdown
    assert "### TITULO PRINCIPAL" in markdown
    assert "- Elemento 1" in markdown
    assert "Texto normal del parrafo." in markdown


def test_calculate_checksum_returns_sha256():
    """Verifica que el hash sea SHA-256 de 64 caracteres."""
    calculador = ChecksumCalculator()

    checksum = calculador.calculate(b"contenido de prueba para hash")

    assert len(checksum) == 64
    assert isinstance(checksum, str)
    int(checksum, 16)  # Verifica que sea hexadecimal


def test_checksum_consistency():
    """Mismo contenido = mismo hash."""
    calculador = ChecksumCalculator()

    hash1 = calculador.calculate(b"contenido consistente")
    hash2 = calculador.calculate(b"contenido consistente")

    assert hash1 == hash2


def test_checksum_different_content():
    """Contenido diferente = hash diferente."""
    calculador = ChecksumCalculator()

    hash1 = calculador.calculate(b"contenido A")
    hash2 = calculador.calculate(b"contenido B")

    assert hash1 != hash2


def test_calculate_checksum_matches_literal():
    """El checksum calculado debe coincidir con el hash SHA-256 pre-calculado.
    Esto evita depender de la misma lógica de `hashlib` dentro del propio test.
    """
    calculador = ChecksumCalculator()
    # Contenido idéntico al usado para generar el hash literal
    data = b"datos de prueba para verificar"

    # Hash SHA-256 generado previamente con `hashlib.sha256(data).hexdigest()`
    expected_literal = (
        "3031af382c85802ddb5f99e73602bf7cef3379374d2dfe5ba1738df3a2c46f5b"
    )
    actual = calculador.calculate(data)

    assert actual == expected_literal
