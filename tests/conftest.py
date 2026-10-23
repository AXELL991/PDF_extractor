"""Configuración común de los tests."""

import pytest

from app.core.rate_limit import limiter


@pytest.fixture(autouse=True)
def desactivar_rate_limiting():
    """Evita que el rate limiting global interfiera entre tests."""
    limiter.enabled = False
    yield
    limiter.enabled = True
