import io
import pytest
from app.services.pdf_extractor import PyPDFExtractor

def test_extract_text_from_pdf():
    """
    Verifica que el extractor pueda procesar un flujo de bytes
    y devolver un string (aunque sea vacío si el PDF no tiene texto).
    """
    extractor = PyPDFExtractor()
    
    # Creamos un archivo PDF vacío en memoria para la prueba
    # (Un PDF mínimo real requiere estructura, pero probamos que la función no explote)
    fake_pdf = io.BytesIO(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF")
    
    resultado = extractor.extract(fake_pdf)
    
    assert isinstance(resultado, str)

def test_calculate_checksum():
    """
    Verifica que el hash generado sea un SHA-256 válido (64 caracteres hexadecimales).
    """
    extractor = PyPDFExtractor()
    content = io.BytesIO(b"contenido de prueba para hash")
    
    checksum = extractor.calculate_checksum(content)
    
    assert len(checksum) == 64
    assert isinstance(checksum, str)
    # Verificar que sea hexadecimal
    int(checksum, 16) 

def test_checksum_consistency():
    """
    Verifica que el mismo contenido siempre genere el mismo hash.
    """
    extractor = PyPDFExtractor()
    content1 = io.BytesIO