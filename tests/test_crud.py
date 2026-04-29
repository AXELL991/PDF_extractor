"""Tests para operaciones CRUD completas."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app

client = TestClient(app)


class TestCreate:
    """Tests para CREATE - Subir PDFs."""

    @patch("app.main.db")
    def test_upload_valid_pdf(self, mock_db):
        """Subir PDF valido guarda en BD."""
        mock_db.obtener_por_checksum.return_value = None
        mock_db.guardar_documento.return_value = Mock(inserted_id="123")

        files = {"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")}
        response = client.post("/upload", files=files)

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "sha256" in response.json()

    def test_upload_no_file(self):
        """Sin archivo devuelve 422."""
        response = client.post("/upload")
        assert response.status_code == 422

    def test_upload_invalid_format(self):
        """Archivo no-PDF devuelve 400."""
        files = {"file": ("test.txt", b"contenido", "text/plain")}
        response = client.post("/upload", files=files)

        assert response.status_code == 400
        assert "no es PDF" in response.json()["detail"]

    @patch("app.main.db")
    def test_upload_duplicate_pdf(self, mock_db):
        """PDF duplicado devuelve 409."""
        mock_db.obtener_por_checksum.return_value = {"archivo": "existente.pdf"}

        files = {"file": ("test.pdf", b"%PDF-1.4 duplicate", "application/pdf")}
        response = client.post("/upload", files=files)

        assert response.status_code == 409
        assert "duplicado" in response.json()["detail"].lower() or "ya fue procesado" in response.json()["detail"]


class TestRead:
    """Tests para READ - Consultar documentos."""

    @patch("app.main.db")
    def test_list_documents_empty(self, mock_db):
        """Lista vacia cuando no hay documentos."""
        mock_db.listar_todos.return_value = []

        response = client.get("/documentos")

        assert response.status_code == 200
        assert response.json()["total"] == 0
        assert response.json()["documentos"] == []

    @patch("app.main.db")
    def test_list_documents_with_data(self, mock_db):
        """Lista documentos existentes."""
        mock_db.listar_todos.return_value = [
            {"archivo": "doc1.pdf", "hash_seguridad": "abc123"},
            {"archivo": "doc2.pdf", "hash_seguridad": "def456"}
        ]

        response = client.get("/documentos")

        assert response.status_code == 200
        assert response.json()["total"] == 2

    @patch("app.main.db")
    def test_get_document_by_checksum_found(self, mock_db):
        """Buscar documento existente."""
        mock_db.obtener_por_checksum.return_value = {
            "archivo": "test.pdf",
            "texto": "contenido",
            "hash_seguridad": "abc123",
            "_id": "mongo_id"
        }

        response = client.get("/documentos/abc123")

        assert response.status_code == 200
        assert response.json()["archivo"] == "test.pdf"
        assert "_id" not in response.json()  # Se elimina el _id

    @patch("app.main.db")
    def test_get_document_by_checksum_not_found(self, mock_db):
        """Buscar documento inexistente devuelve 404."""
        mock_db.obtener_por_checksum.return_value = None

        response = client.get("/documentos/noexiste")

        assert response.status_code == 404


class TestUpdate:
    """Tests para UPDATE - Actualizar documentos."""

    @patch("app.main.db")
    def test_update_document_name_success(self, mock_db):
        """Actualizar nombre de documento existente."""
        mock_db.obtener_por_checksum.return_value = {"archivo": "viejo.pdf"}
        mock_db.actualizar_nombre.return_value = Mock(modified_count=1)

        response = client.put(
            "/documentos/abc123",
            json={"nuevo_nombre": "nuevo.pdf"}
        )

        assert response.status_code == 200
        assert "nuevo.pdf" in response.json()["message"]

    @patch("app.main.db")
    def test_update_document_not_found(self, mock_db):
        """Actualizar documento inexistente devuelve 404."""
        mock_db.obtener_por_checksum.return_value = None

        response = client.put(
            "/documentos/noexiste",
            json={"nuevo_nombre": "nuevo.pdf"}
        )

        assert response.status_code == 404


class TestDelete:
    """Tests para DELETE - Eliminar documentos."""

    @patch("app.main.db")
    def test_delete_document_success(self, mock_db):
        """Eliminar documento existente."""
        mock_db.obtener_por_checksum.return_value = {"archivo": "borrar.pdf"}
        mock_db.eliminar_documento.return_value = Mock(deleted_count=1)

        response = client.delete("/documentos/abc123")

        assert response.status_code == 200
        assert "eliminado" in response.json()["message"].lower()

    @patch("app.main.db")
    def test_delete_document_not_found(self, mock_db):
        """Eliminar documento inexistente devuelve 404."""
        mock_db.obtener_por_checksum.return_value = None

        response = client.delete("/documentos/noexiste")

        assert response.status_code == 404
