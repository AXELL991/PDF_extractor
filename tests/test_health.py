"""Tests de contrato HTTP para los endpoints de estado (/ , /health, /security.txt).

La app real se monta con un `FakeRepo` en memoria publicado en
`app.state.repositorio`, el mismo seam que usa el composition root.
"""

from fastapi.testclient import TestClient

from tests.fakes import FakeRepo, build_test_app


def client_for(repositorio: FakeRepo) -> TestClient:
    return TestClient(build_test_app(repositorio), base_url="http://localhost")


def test_root_devuelve_200_y_schema_esperado():
    """GET / retorna 200 con información básica de estado de la API."""
    fake_db = FakeRepo()
    client = client_for(fake_db)

    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "online"
    assert "message" in body
    assert "environment" in body
    assert "version" in body


def test_health_devuelve_200_y_schema_esperado():
    """GET /health retorna 200 y el payload de salud con base de datos conectada."""
    fake_db = FakeRepo()
    client = client_for(fake_db)

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["database"] == "connected"
    assert "timestamp" in body
    assert "version" in body
    assert "environment" in body


def test_security_txt_devuelve_200_y_contenido_plano():
    """GET /security.txt retorna 200 con texto plano según RFC 9116."""
    fake_db = FakeRepo()
    client = client_for(fake_db)

    response = client.get("/security.txt")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "Contact: mailto:security@utn.edu.ar" in response.text
    assert "Expires:" in response.text
    assert "Policy:" in response.text
