"""Configuración común de los tests."""

import os

import pytest

# La configuración debe leerse antes de importar `app.main` o `app.core.config`.
# En tests usamos desarrollo para no depender del entorno del host.
os.environ.setdefault("ENVIRONMENT", "development")

from app.core.rate_limit import limiter  # noqa: E402


@pytest.fixture(autouse=True)
def desactivar_rate_limiting():
    """Evita que el rate limiting global interfiera entre tests."""
    limiter.enabled = False
    yield
    limiter.enabled = True


def crear_pdf_con_texto(texto: str = "Hola PDF de prueba") -> bytes:
    """Genera un PDF mínimo válido con una página y texto extraíble."""
    texto_pdf = texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
        ),
        b"",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    stream = f"BT /F1 24 Tf 72 720 Td ({texto_pdf}) Tj ET".encode("latin-1")
    objetos[3] = (
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream"
    )

    salida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for numero, objeto in enumerate(objetos, start=1):
        offsets.append(len(salida))
        salida += f"{numero} 0 obj\n".encode("ascii") + objeto + b"\nendobj\n"

    posicion_xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n".encode("ascii")
    salida += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        salida += f"{offset:010d} 00000 n \n".encode("ascii")
    salida += (
        f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
        f"startxref\n{posicion_xref}\n%%EOF\n"
    ).encode("ascii")

    return bytes(salida)


@pytest.fixture
def pdf_con_texto() -> bytes:
    """PDF válido con el texto 'Hola PDF de prueba'."""
    return crear_pdf_con_texto()
