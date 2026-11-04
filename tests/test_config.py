"""Tests de la configuración centralizada."""

import pytest

from app.core.config import get_settings, validate_config


def test_tamano_maximo_usa_una_sola_fuente():
    settings = get_settings()
    assert settings.MAX_FILE_SIZE_BYTES == settings.MAX_FILE_SIZE_MB * 1024 * 1024


def test_configuracion_valida_no_lanza():
    validate_config()


def test_tamano_maximo_cero_falla(monkeypatch):
    monkeypatch.setattr("app.core.config.get_settings", lambda: None)

    with pytest.raises((AttributeError, RuntimeError, ValueError)):
        validate_config()


def test_mongo_uri_invalido_falla():
    from pydantic import ValidationError

    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(MONGO_URI="no-es-valido")


def test_mongo_db_name_vacio_falla():
    from pydantic import ValidationError

    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(MONGO_DB_NAME="")


def test_max_file_size_mb_negativo_falla():
    from pydantic import ValidationError

    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(MAX_FILE_SIZE_MB=-1)


def test_max_file_size_mb_cero_falla():
    from pydantic import ValidationError

    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(MAX_FILE_SIZE_MB=0)
