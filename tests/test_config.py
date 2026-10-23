"""Tests de la configuración centralizada y del fail-fast de producción."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.config import (
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    SESSION_SECRET_KEY,
    get_session_secret_key,
    validate_config,
)


def test_tamano_maximo_usa_una_sola_fuente():
    assert MAX_FILE_SIZE_BYTES == MAX_FILE_SIZE_MB * 1024 * 1024


def test_produccion_sin_session_secret_falla():
    with pytest.raises(RuntimeError, match="SESSION_SECRET_KEY"):
        validate_config("production", "")


def test_produccion_con_session_secret_es_valida():
    validate_config("production", "secreto-de-produccion")


def test_desarrollo_permite_ausencia_de_session_secret():
    validate_config("development", "")


def test_get_session_secret_key_en_tests():
    assert get_session_secret_key() == SESSION_SECRET_KEY


def test_app_falla_al_importar_en_produccion_sin_secret():
    entorno = os.environ.copy()
    entorno["ENVIRONMENT"] = "production"
    entorno.pop("SESSION_SECRET_KEY", None)
    raiz = Path(__file__).resolve().parents[1]

    resultado = subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=raiz,
        env=entorno,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )

    assert resultado.returncode != 0
    assert "SESSION_SECRET_KEY" in resultado.stderr
