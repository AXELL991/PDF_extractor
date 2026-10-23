"""Tests de contrato HTTP para el CRUD.

La app real se monta con un `FakeRepo` en memoria publicado en
`app.state.repositorio`, el mismo seam que usa el composition root.
"""

import hashlib

from fastapi.testclient import TestClient

from app.domain.entities import Documento
from tests.fakes import FakeRepo, build_test_app


CHECKSUM_EXISTENTE = "a" * 64
CHECKSUM_INEXISTENTE = "f" * 64


def client_for(repositorio: FakeRepo) -> TestClient:
    return TestClient(build_test_app(repositorio), base_url="http://localhost")


class TestCreate:
    """Tests for the upload endpoint."""

    def test_upload_valid_pdf(self, pdf_con_texto):
        fake_db = FakeRepo()
        client = client_for(fake_db)

        files = {"file": ("test.pdf", pdf_con_texto, "application/pdf")}
        response = client.post("/upload", files=files)

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "sha256" in response.json()
        assert fake_db.guardado is not None
        assert fake_db.guardado.archivo == "test.pdf"
        assert "Hola PDF de prueba" in fake_db.guardado.texto
        assert fake_db.guardado.hash_seguridad in fake_db.documentos

    def test_upload_no_file(self):
        response = client_for(FakeRepo()).post("/upload")
        assert response.status_code == 422

    def test_upload_invalid_format(self):
        files = {"file": ("test.txt", b"contenido", "text/plain")}
        response = client_for(FakeRepo()).post("/upload", files=files)
        assert response.status_code == 400
        assert "no es un PDF" in response.json()["detail"]

    def test_upload_invalid_content(self):
        files = {"file": ("test.pdf", b"no es un pdf", "application/pdf")}
        response = client_for(FakeRepo()).post("/upload", files=files)
        assert response.status_code == 400
        assert "no es un PDF" in response.json()["detail"]

    def test_upload_corrupt_pdf_with_header(self):
        files = {
            "file": ("test.pdf", b"%PDF-1.4 contenido corrupto", "application/pdf")
        }
        response = client_for(FakeRepo()).post("/upload", files=files)
        assert response.status_code == 400
        assert "no es un PDF" in response.json()["detail"]

    def test_upload_duplicate_pdf(self, pdf_con_texto):
        checksum = hashlib.sha256(pdf_con_texto).hexdigest()
        fake_db = FakeRepo(
            [Documento(archivo="existente.pdf", hash_seguridad=checksum)]
        )

        files = {"file": ("test.pdf", pdf_con_texto, "application/pdf")}
        response = client_for(fake_db).post("/upload", files=files)

        assert response.status_code == 409
        assert fake_db.guardado is None


class TestRead:
    """Tests for GET endpoints."""

    def test_list_documents_empty(self):
        response = client_for(FakeRepo()).get("/documentos")
        assert response.status_code == 200
        assert response.json()["total"] == 0
        assert response.json()["documentos"] == []

    def test_list_documents_with_data(self):
        fake_db = FakeRepo(
            [
                Documento(archivo="doc1.pdf", hash_seguridad=CHECKSUM_EXISTENTE),
                Documento(archivo="doc2.pdf", hash_seguridad="b" * 64),
            ]
        )
        response = client_for(fake_db).get("/documentos")
        assert response.status_code == 200
        assert response.json()["total"] == 2

    def test_get_document_by_checksum_found(self):
        fake_db = FakeRepo(
            [
                Documento(
                    archivo="test.pdf",
                    texto="contenido",
                    hash_seguridad=CHECKSUM_EXISTENTE,
                )
            ]
        )
        response = client_for(fake_db).get(f"/documentos/{CHECKSUM_EXISTENTE}")
        assert response.status_code == 200
        assert response.json()["archivo"] == "test.pdf"

    def test_get_document_by_checksum_not_found(self):
        response = client_for(FakeRepo()).get(f"/documentos/{CHECKSUM_INEXISTENTE}")
        assert response.status_code == 404

    def test_get_document_invalid_checksum(self):
        response = client_for(FakeRepo()).get("/documentos/123")
        assert response.status_code == 400


class TestUpdate:
    """Tests for the PUT endpoint."""

    def test_update_document_name_success(self):
        fake_db = FakeRepo(
            [
                Documento(
                    archivo="viejo.pdf",
                    hash_seguridad=CHECKSUM_EXISTENTE,
                )
            ]
        )
        response = client_for(fake_db).put(
            f"/documentos/{CHECKSUM_EXISTENTE}",
            json={"nuevo_nombre": "nuevo.pdf"},
        )
        assert response.status_code == 200
        assert "nuevo.pdf" in response.json()["message"]
        assert fake_db.documentos[CHECKSUM_EXISTENTE].archivo == "nuevo.pdf"

    def test_update_document_not_found(self):
        response = client_for(FakeRepo()).put(
            f"/documentos/{CHECKSUM_INEXISTENTE}",
            json={"nuevo_nombre": "nuevo.pdf"},
        )
        assert response.status_code == 404


class TestDelete:
    """Tests for the DELETE endpoint."""

    def test_delete_document_success(self):
        fake_db = FakeRepo(
            [
                Documento(
                    archivo="borrar.pdf",
                    hash_seguridad=CHECKSUM_EXISTENTE,
                )
            ]
        )
        response = client_for(fake_db).delete(f"/documentos/{CHECKSUM_EXISTENTE}")
        assert response.status_code == 200
        assert "eliminado" in response.json()["message"].lower()
        assert CHECKSUM_EXISTENTE not in fake_db.documentos

    def test_delete_document_not_found(self):
        response = client_for(FakeRepo()).delete(f"/documentos/{CHECKSUM_INEXISTENTE}")
        assert response.status_code == 404
