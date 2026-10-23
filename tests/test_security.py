"""Security helper tests for the PDF extractor project.
These tests validate the core security utilities without touching the
application server or database.
"""

import pytest
from app.core.security import (
    generate_request_id,
    is_valid_pdf,
    sanitize_filename,
    sanitize_text,
    validate_checksum,
)


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("documento.pdf", "documento.pdf"),
        ("../escape.pdf", "escape.pdf"),  # path traversal stripped
        ("mal<script>.pdf", "mal.pdf"),  # HTML stripped
    ],
)
def test_sanitize_filename_valid(filename, expected):
    assert sanitize_filename(filename) == expected


def test_sanitize_filename_invalid():
    with pytest.raises(ValueError):
        sanitize_filename("archivo.exe")  # not a .pdf extension
    with pytest.raises(ValueError):
        sanitize_filename("")  # empty string


def test_sanitize_filename_quita_puntos_y_espacios_extremos():
    assert sanitize_filename("  .documento.pdf.  ") == "documento.pdf"


@pytest.mark.parametrize(
    "checksum,valid",
    [
        ("a" * 64, True),
        ("f" * 64, True),
        ("123", False),
        ("g" * 64, False),  # non‑hex character
    ],
)
def test_validate_checksum(checksum, valid):
    if valid:
        # Should not raise
        validate_checksum(checksum)
    else:
        with pytest.raises(ValueError):
            validate_checksum(checksum)


def test_validate_checksum_rechaza_no_string():
    with pytest.raises(ValueError):
        validate_checksum(123)


def test_sanitize_text_removes_html():
    resultado = sanitize_text("<script>alert('xss')</script>Hola <b>mundo</b>")
    assert "<script>" not in resultado
    assert "<b>" not in resultado
    assert "Hola" in resultado


def test_sanitize_text_vacio_devuelve_vacio():
    assert sanitize_text("") == ""


def test_is_valid_pdf_true(pdf_con_texto):
    assert is_valid_pdf(pdf_con_texto)


def test_is_valid_pdf_false():
    assert not is_valid_pdf(b"not a pdf")


def test_is_valid_pdf_rejects_header_only():
    assert not is_valid_pdf(b"%PDF-1.4 contenido corrupto")


def test_is_valid_pdf_rejects_empty_content():
    assert not is_valid_pdf(b"")


def test_generate_request_id_es_unico_y_seguro():
    primero = generate_request_id()
    segundo = generate_request_id()

    assert primero != segundo
    assert len(primero) >= 32


def test_generate_request_id_es_urlsafe():
    request_id = generate_request_id()

    assert request_id.replace("-", "").replace("_", "").isalnum()
