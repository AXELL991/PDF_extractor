"""Security helper tests for the PDF extractor project.
These tests validate the core security utilities without touching the
application server or database.
"""

import pytest
from app.core.security import (
    generate_csrf_token,
    is_safe_ip,
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
        ("mal<script>.pdf", "mal.pdf"),   # HTML stripped
    ],
)
def test_sanitize_filename_valid(filename, expected):
    assert sanitize_filename(filename) == expected


def test_sanitize_filename_invalid():
    with pytest.raises(ValueError):
        sanitize_filename("archivo.exe")  # not a .pdf extension
    with pytest.raises(ValueError):
        sanitize_filename("")  # empty string


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


def test_sanitize_text_removes_html():
    resultado = sanitize_text("<script>alert('xss')</script>Hola <b>mundo</b>")
    assert "<script>" not in resultado
    assert "<b>" not in resultado
    assert "Hola" in resultado


def test_is_valid_pdf_true(pdf_con_texto):
    assert is_valid_pdf(pdf_con_texto)


def test_is_valid_pdf_false():
    assert not is_valid_pdf(b"not a pdf")


def test_is_valid_pdf_rejects_header_only():
    assert not is_valid_pdf(b"%PDF-1.4 contenido corrupto")


def test_is_valid_pdf_rejects_empty_content():
    assert not is_valid_pdf(b"")


@pytest.mark.parametrize(
    "client_ip,expected",
    [
        ("127.0.0.1", True),
        ("10.1.2.3", True),
        ("172.16.0.1", True),
        ("192.168.1.25", True),
        ("::1", True),
        ("8.8.8.8", False),
        ("172.32.0.1", False),
        ("no-es-una-ip", False),
    ],
)
def test_is_safe_ip_default_networks(client_ip, expected):
    assert is_safe_ip(client_ip) is expected


def test_is_safe_ip_custom_networks():
    assert is_safe_ip("203.0.113.10", ["203.0.113.0/24"])
    assert not is_safe_ip("198.51.100.10", ["203.0.113.0/24"])


def test_generate_csrf_token_es_unico_y_seguro():
    primero = generate_csrf_token()
    segundo = generate_csrf_token()

    assert primero != segundo
    assert len(primero) >= 32
