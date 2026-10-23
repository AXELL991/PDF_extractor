"""Tests de la application factory y de la inyección de dependencias."""

from fastapi.testclient import TestClient

from app.main import create_app
from tests.fakes import FakeExtractor, FakeRepo


def test_create_app_inyecta_repositorio_y_extractor(pdf_con_texto):
    repo = FakeRepo()
    extractor = FakeExtractor(texto="Texto inyectado por el fake")

    app = create_app(repositorio=repo, extractor=extractor)

    assert app.state.repositorio is repo
    assert app.state.extractor is extractor

    client = TestClient(app, base_url="http://localhost")
    response = client.post(
        "/upload",
        files={"file": ("test.pdf", pdf_con_texto, "application/pdf")},
    )

    assert response.status_code == 200
    assert repo.guardado is not None
    assert repo.guardado.texto == "Texto inyectado por el fake"
