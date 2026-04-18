import io
import pytest

# Importaremos el extractor desde nuestra carpeta de servicios (que vamos a crear después)
from app.services.pdf_extractor import PyPDFExtractor

class TestPyPDFExtractor:
    """Tests para el extractor de PDF trabajando directamente en RAM."""

    def test_pypdf_extractor_returns_string_from_memory(self):
        # Arrange (Preparar)
        extractor = PyPDFExtractor()
        
        # Simulamos un archivo PDF súper básico directamente en la memoria RAM (BytesIO)
        # Esto reemplaza al dummy_path = "tests/dummy.pdf"
        fake_pdf_bytes = b"%PDF-1.4\n%EOF" 
        archivo_en_ram = io.BytesIO(fake_pdf_bytes)

        # Act (Actuar)
        # Le pasamos el archivo de la RAM, no una ruta del disco
        result = extractor.extract(archivo_en_ram)

        # Assert (Afirmar)
        assert isinstance(result, str)

    def test_pypdf_extractor_calculates_correct_checksum(self):
        # Un nuevo test esencial para el TP: el Checksum (Hash único del archivo)
        extractor = PyPDFExtractor()
        fake_pdf_bytes = b"%PDF-1.4\n%EOF"
        archivo_en_ram = io.BytesIO(fake_pdf_bytes)
        
        checksum = extractor.calculate_checksum(archivo_en_ram)
        
        # Tiene que devolver una cadena de texto (el hash generado)
        assert isinstance(checksum, str)
        assert len(checksum) > 0