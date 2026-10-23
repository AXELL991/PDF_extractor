"""Tests de contrato para endpoints auxiliares y health checks."""

from fastapi.testclient import TestClient

from tests.fakes import FakeRepo, build_test_app


def client_for(repositorio: FakeRepo) -> TestClient:
    return TestClient(build_test_app(repositorio), base_url="http://localhost")


class TestRootEndpoint:
    def test_root_responde_200(self, client):
        response = client.get("/")

        assert response.status_code == 200
        assert response.json()["status"] == "online"
        assert "message" in response.json()


class TestHealthEndpoint:
    def test_health_200_cuando_ping_funciona(self, client, fake_repo):
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["database"] == "connected"
        assert fake_repo.llamadas == [("ping",)]

    def test_health_503_cuando_ping_falla(self):
        repo = FakeRepo(ping_error=RuntimeError("Mongo no disponible"))

        response = client_for(repo).get("/health")

        assert response.status_code == 503
        assert response.json()["status"] == "unhealthy"
        assert response.json()["database"] == "disconnected"
        assert repo.llamadas == [("ping",)]


class TestSecurityTxt:
    def test_security_txt_responde_texto_plano(self, client):
        response = client.get("/security.txt")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert "Contact: mailto:" in response.text
        assert "Policy:" in response.text
