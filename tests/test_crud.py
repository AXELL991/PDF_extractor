"""Tests for CRUD operations using a fake repository.
These tests no longer patch `app.main.db`; instead they construct a lightweight
`FakeRepo` that implements the minimal MongoRepository interface required by
the use case and router.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from app.main import app as base_app
from app.use_cases.procesar_documento import ProcesarDocumentoUseCase
from app.services.pdf_extractor import PyPDFExtractor
from app.api.routes import build_router

# ---------------------------------------------------------------------------
# Helper fake repository used by the tests
# ---------------------------------------------------------------------------
class FakeRepo:
    """In‑memory stand‑in for `MongoRepository`.
    Tests set the appropriate return attributes before each request.
    """

    # Default return values (can be overwritten by each test)
    obtener_por_checksum_return = None
    guardar_documento_return = None
    listar_todos_return = []
    actualizar_nombre_return = None
    eliminar_documento_return = None

    # Call‑tracking flags
    guardar_documento_called = False

    def obtener_por_checksum(self, checksum: str):
        return self.obtener_por_checksum_return

    def guardar_documento(self, documento):
        self.guardar_documento_called = True
        return self.guardar_documento_return

    def listar_todos(self):
        return self.listar_todos_return

    def actualizar_nombre(self, checksum: str, nuevo_nombre: str):
        return self.actualizar_nombre_return

    def eliminar_documento(self, checksum: str):
        return self.eliminar_documento_return

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CHECKSUM_EXISTENTE = "a" * 64
CHECKSUM_INEXISTENTE = "f" * 64

# ---------------------------------------------------------------------------
# Helper to build a FastAPI app with a fake repo injected
# ---------------------------------------------------------------------------
def get_test_app(fake_repo: FakeRepo):
    extractor = PyPDFExtractor()
    use_case = ProcesarDocumentoUseCase(extractor=extractor, db=fake_repo)
    test_app = base_app.__class__(
        title=base_app.title,
        description=base_app.description,
        version=base_app.version,
    )
    test_app.include_router(build_router(lambda: fake_repo, use_case))
    return test_app

# ---------------------------------------------------------------------------
# CREATE tests
# ---------------------------------------------------------------------------
class TestCreate:
    """Tests for the upload endpoint."""

    def test_upload_valid_pdf(self):
        fake_db = FakeRepo()
        fake_db.obtener_por_checksum_return = None
        fake_db.guardar_documento_return = Mock(inserted_id="123")
        client = TestClient(get_test_app(fake_db), base_url="http://localhost")

        files = {"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")}
        response = client.post("/upload", files=files)

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "sha256" in response.json()
        assert fake_db.guardar_documento_called

    def test_upload_no_file(self):
        client = TestClient(get_test_app(FakeRepo()), base_url="http://localhost")
        response = client.post("/upload")
        assert response.status_code == 422

    def test_upload_invalid_format(self):
        client = TestClient(get_test_app(FakeRepo()), base_url="http://localhost")
        files = {"file": ("test.txt", b"contenido", "text/plain")}
        response = client.post("/upload", files=files)
        assert response.status_code == 400
        assert "no es un PDF" in response.json()["detail"]

    def test_upload_duplicate_pdf(self):
        fake_db = FakeRepo()
        fake_db.obtener_por_checksum_return = {"archivo": "existente.pdf"}
        client = TestClient(get_test_app(fake_db), base_url="http://localhost")
        files = {"file": ("test.pdf", b"%PDF-1.4 duplicate", "application/pdf")}
        response = client.post("/upload", files=files)
        assert response.status_code == 409

# ---------------------------------------------------------------------------
# READ tests
# ---------------------------------------------------------------------------
class TestRead:
    """Tests for GET endpoints."""

    def test_list_documents_empty(self):
        fake_db = FakeRepo()
        fake_db.listar_todos_return = []
        client = TestClient(get_test_app(fake_db), base_url="http://localhost")
        response = client.get("/documentos")
        assert response.status_code == 200
        assert response.json()["total"] == 0
        assert response.json()["documentos"] == []

    def test_list_documents_with_data(self):
        fake_db = FakeRepo()
        fake_db.listar_todos_return = [
            {"archivo": "doc1.pdf", "hash_seguridad": CHECKSUM_EXISTENTE},
            {"archivo": "doc2.pdf", "hash_seguridad": "b" * 64},
        ]
        client = TestClient(get_test_app(fake_db), base_url="http://localhost")
        response = client.get("/documentos")
        assert response.status_code == 200
        assert response.json()["total"] == 2

    def test_get_document_by_checksum_found(self):
        fake_db = FakeRepo()
        fake_db.obtener_por_checksum_return = {
            "archivo": "test.pdf",
            "texto": "contenido",
            "hash_seguridad": CHECKSUM_EXISTENTE,
            "_id": "mongo_id",
        }
        client = TestClient(get_test_app(fake_db), base_url="http://localhost")
        response = client.get(f"/documentos/{CHECKSUM_EXISTENTE}")
        assert response.status_code == 200
        assert response.json()["archivo"] == "test.pdf"
        assert "_id" not in response.json()

    def test_get_document_by_checksum_not_found(self):
        fake_db = FakeRepo()
        fake_db.obtener_por_checksum_return = None
        client = TestClient(get_test_app(fake_db), base_url="http://localhost")
        response = client.get(f"/documentos/{CHECKSUM_INEXISTENTE}")
        assert response.status_code == 404

# ---------------------------------------------------------------------------
# UPDATE tests
# ---------------------------------------------------------------------------
class TestUpdate:
    """Tests for the PUT endpoint."""

    def test_update_document_name_success(self):
        fake_db = FakeRepo()
        fake_db.obtener_por_checksum_return = {"archivo": "viejo.pdf"}
        fake_db.actualizar_nombre_return = Mock(modified_count=1)
        client = TestClient(get_test_app(fake_db), base_url="http://localhost")
        response = client.put(
            f"/documentos/{CHECKSUM_EXISTENTE}",
            json={"nuevo_nombre": "nuevo.pdf"},
        )
        assert response.status_code == 200
        assert "nuevo.pdf" in response.json()["message"]

    def test_update_document_not_found(self):
        fake_db = FakeRepo()
        fake_db.obtener_por_checksum_return = None
        client = TestClient(get_test_app(fake_db), base_url="http://localhost")
        response = client.put(
            f"/documentos/{CHECKSUM_INEXISTENTE}",
            json={"nuevo_nombre": "nuevo.pdf"},
        )
        assert response.status_code == 404

# ---------------------------------------------------------------------------
# DELETE tests
# ---------------------------------------------------------------------------
class TestDelete:
    """Tests for the DELETE endpoint."""

    def test_delete_document_success(self):
        fake_db = FakeRepo()
        fake_db.obtener_por_checksum_return = {"archivo": "borrar.pdf"}
        fake_db.eliminar_documento_return = Mock(deleted_count=1)
        client = TestClient(get_test_app(fake_db), base_url="http://localhost")
        response = client.delete(f"/documentos/{CHECKSUM_EXISTENTE}")
        assert response.status_code == 200
        assert "eliminado" in response.json()["message"].lower()

    def test_delete_document_not_found(self):
        fake_db = FakeRepo()
        fake_db.obtener_por_checksum_return = None
        client = TestClient(get_test_app(fake_db), base_url="http://localhost")
        response = client.delete(f"/documentos/{CHECKSUM_INEXISTENTE}")
        assert response.status_code == 404
