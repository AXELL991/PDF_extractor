import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_upload_pdf_no_file():
    # Probar que falla si no mandamos nada
    response = client.post("/upload")
    assert response.status_code == 422 

def test_upload_invalid_format():
    # Probar que falla si mandamos un .txt en vez de .pdf
    files = {"file": ("test.txt", b"contenido falso", "text/plain")}
    response = client.post("/upload", files=files)
    assert response.status_code == 400
    assert "no es PDF" in response.json()["detail"]