"""Tests para excepciones personalizadas del dominio."""

import pytest

from app.core.config import get_settings
from app.domain.exceptions import (
    DocumentoDuplicadoError,
    DocumentoNoEncontradoError,
    DomainException,
    ExtractionError,
    FormatoInvalidoError,
    NombreArchivoInvalidoError,
    TamañoExcedidoError,
)

MAX_FILE_SIZE_MB = get_settings().MAX_FILE_SIZE_MB


def test_domain_exception_base():
    """Excepción base tiene message."""
    exc = DomainException("Error genérico")

    assert exc.message == "Error genérico"
    assert str(exc) == "Error genérico"


def test_formato_invalido_error():
    """Error de formato."""
    exc = FormatoInvalidoError()

    assert "no es PDF" in exc.message


def test_tamaño_excedido_error_default():
    """Error de tamaño usa el mensaje por defecto."""
    exc = TamañoExcedidoError()

    assert "tamaño máximo" in exc.message


def test_tamaño_excedido_error_custom():
    """Error de tamaño acepta mensaje custom."""
    exc = TamañoExcedidoError("Archivo demasiado grande")

    assert "Archivo demasiado grande" in exc.message


def test_documento_duplicado_error():
    """Error de duplicado."""
    exc = DocumentoDuplicadoError()

    assert "duplicado" in exc.message.lower() or "ya fue procesado" in exc.message


def test_documento_no_encontrado_error():
    """Error de no encontrado."""
    exc = DocumentoNoEncontradoError()

    assert "no encontrado" in exc.message.lower()


def test_extraction_error():
    """Error de extracción."""
    exc = ExtractionError()

    assert "extraer" in exc.message.lower()


def test_nombre_archivo_invalido_error():
    """Error de nombre de archivo inválido."""
    exc = NombreArchivoInvalidoError()

    assert "inválido" in exc.message.lower()


def test_documento_invalido_error():
    """Error de documento inválido."""
    from app.domain.exceptions import DocumentoInvalidoError

    exc = DocumentoInvalidoError()

    assert "inválido" in exc.message.lower()


def test_documento_invalido_usa_excepcion_de_dominio():
    """Instanciar Documento inválido lanza DocumentoInvalidoError de app.domain.exceptions."""
    from app.domain.entities import Documento
    from app.domain.exceptions import DocumentoInvalidoError

    with pytest.raises(DocumentoInvalidoError):
        Documento(archivo="")
