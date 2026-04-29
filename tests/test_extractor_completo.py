"""Tests completos para el extractor de PDF."""
import io
import hashlib
import pytest
from app.services.pdf_extractor import PyPDFExtractor


def test_extract_text_from_pdf():
    """Verifica que el extractor devuelva un string."""
    extractor = PyPDFExtractor()
    fake_pdf = io.BytesIO(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF")

    resultado = extractor.extract(fake_pdf)

    assert isinstance(resultado, str)


def test_calculate_checksum_returns_sha256():
    """Verifica que el hash sea SHA-256 de 64 caracteres."""
    extractor = PyPDFExtractor()
    content = io.BytesIO(b"contenido de prueba para hash")

    checksum = extractor.calculate_checksum(content)

    assert len(checksum) == 64
    assert isinstance(checksum, str)
    int(checksum, 16)  # Verifica que sea hexadecimal


def test_checksum_consistency():
    """Mismo contenido = mismo hash."""
    extractor = PyPDFExtractor()
    content1 = io.BytesIO(b"contenido consistente")
    content2 = io.BytesIO(b"contenido consistente")

    hash1 = extractor.calculate_checksum(content1)
    hash2 = extractor.calculate_checksum(content2)

    assert hash1 == hash2


def test_checksum_different_content():
    """Contenido diferente = hash diferente."""
    extractor = PyPDFExtractor()
    content1 = io.BytesIO(b"contenido A")
    content2 = io.BytesIO(b"contenido B")

    hash1 = extractor.calculate_checksum(content1)
    hash2 = extractor.calculate_checksum(content2)

    assert hash1 != hash2


def test_calculate_checksum_matches_hashlib():
    """El checksum debe coincidir con hashlib.sha256."""
    extractor = PyPDFExtractor()
    data = b"datos de prueba para verificar"
    content = io.BytesIO(data)

    expected = hashlib.sha256(data).hexdigest()
    actual = extractor.calculate_checksum(content)

    assert actual == expected
