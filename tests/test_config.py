"""Tests de la configuración centralizada."""

import pytest

from app.core.config import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB, validate_config


def test_tamano_maximo_usa_una_sola_fuente():
    assert MAX_FILE_SIZE_BYTES == MAX_FILE_SIZE_MB * 1024 * 1024


def test_configuracion_valida_no_lanza():
    validate_config()


def test_tamano_maximo_cero_falla(monkeypatch):
    monkeypatch.setattr("app.core.config.MAX_FILE_SIZE_MB", 0)

    with pytest.raises(RuntimeError, match="MAX_FILE_SIZE_MB"):
        validate_config()


def test_tamano_maximo_negativo_falla(monkeypatch):
    monkeypatch.setattr("app.core.config.MAX_FILE_SIZE_MB", -1)

    with pytest.raises(RuntimeError, match="MAX_FILE_SIZE_MB"):
        validate_config()
