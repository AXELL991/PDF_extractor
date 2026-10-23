"""Tests para excepciones personalizadas."""

from app.core.config import MAX_FILE_SIZE_MB
from app.exceptions import (
    DocumentoDuplicadoError,
    DocumentoNoEncontradoError,
    DomainException,
    ExtractionError,
    FormatoInvalidoError,
    TamañoExcedidoError,
)


def test_domain_exception_base():
    """Excepcion base tiene message y status_code."""
    exc = DomainException("Error generico", 418)

    assert exc.message == "Error generico"
    assert exc.status_code == 418
    assert str(exc) == "Error generico"


def test_formato_invalido_error():
    """Error de formato devuelve 400."""
    exc = FormatoInvalidoError()

    assert exc.status_code == 400
    assert "no es PDF" in exc.message


def test_tamaño_excedido_error_default():
    """Error de tamaño usa el límite centralizado de configuración."""
    exc = TamañoExcedidoError()

    assert exc.status_code == 413
    assert f"{MAX_FILE_SIZE_MB}MB" in exc.message


def test_tamaño_excedido_error_custom():
    """Error de tamaño acepta tamaño custom."""
    exc = TamañoExcedidoError(10)

    assert "10MB" in exc.message


def test_documento_duplicado_error():
    """Error de duplicado devuelve 409."""
    exc = DocumentoDuplicadoError()

    assert exc.status_code == 409
    assert "duplicado" in exc.message.lower() or "ya fue procesado" in exc.message


def test_documento_no_encontrado_error():
    """Error de no encontrado devuelve 404."""
    exc = DocumentoNoEncontradoError()

    assert exc.status_code == 404
    assert "no encontrado" in exc.message.lower()


def test_extraction_error_devuelve_422():
    """Un fallo de extracción se reporta como error de dominio 422."""
    exc = ExtractionError()

    assert exc.status_code == 422
    assert "extraer" in exc.message.lower()
