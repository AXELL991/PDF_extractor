"""Tests completos para el extractor de PDF a Markdown."""
import io
from app.services.pdf_extractor import PyPDFExtractor


def test_extract_text_from_pdf(pdf_con_texto):
    """Verifica que el extractor devuelva el texto real de un PDF válido."""
    extractor = PyPDFExtractor()
    resultado = extractor.extract(io.BytesIO(pdf_con_texto))

    assert "Hola PDF de prueba" in resultado
    assert "## Página 1" in resultado


def test_format_page_to_markdown():
    """Verifica la conversion estructurada a Markdown."""
    extractor = PyPDFExtractor()
    texto_ejemplo = "TITULO PRINCIPAL:\n- Elemento 1\n- Elemento 2\nTexto normal del parrafo."
    markdown = extractor._format_page_to_markdown(texto_ejemplo, 1)

    assert "## Página 1" in markdown
    assert "### TITULO PRINCIPAL" in markdown
    assert "- Elemento 1" in markdown
    assert "Texto normal del parrafo." in markdown


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


def test_calculate_checksum_matches_literal():
    """El checksum calculado debe coincidir con el hash SHA-256 pre-calculado.
    Esto evita depender de la misma lógica de `hashlib` dentro del propio test.
    """
    extractor = PyPDFExtractor()
    # Contenido idéntico al usado para generar el hash literal
    data = b"datos de prueba para verificar"
    content = io.BytesIO(data)

    # Hash SHA-256 generado previamente con `hashlib.sha256(data).hexdigest()`
    expected_literal = "3031af382c85802ddb5f99e73602bf7cef3379374d2dfe5ba1738df3a2c46f5b"
    actual = extractor.calculate_checksum(content)

    assert actual == expected_literal
