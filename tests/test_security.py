"""Security helper tests for the PDF extractor project.
These tests validate the core security utilities without touching the
application server or database.
"""

import pytest
from app.core.security import (
    sanitize_filename,
    validate_checksum,
    is_valid_pdf,
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


def _minimal_pdf_bytes():
    """Return a tiny valid PDF (just the header and EOF) as bytes.
    This is sufficient for `is_valid_pdf` which only checks magic numbers.
    """
    return b"%PDF-1.4\n%âãÏÓ\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


def test_is_valid_pdf_true():
    assert is_valid_pdf(_minimal_pdf_bytes())


def test_is_valid_pdf_false():
    assert not is_valid_pdf(b"not a pdf")
