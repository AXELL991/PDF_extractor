import io
import hashlib
from pypdf import PdfReader

class PyPDFExtractor:
    """Clase encargada de la lógica de negocio: extraer texto y generar hash."""

    def extract(self, file_stream: io.BytesIO) -> str:
        """Recibe un flujo de bytes en RAM y devuelve el texto del PDF."""
        try:
            # Leemos el PDF directamente desde el flujo de memoria
            reader = PdfReader(file_stream)
            text = ""
            for page in reader.pages:
                # El 'or ""' evita errores si una página está vacía
                text += page.extract_text() or ""
            return text.strip()
        except Exception as e:
            # Es buena práctica imprimir el error para debuguear
            print(f"[!] Error en la extracción: {e}")
            return ""

    def calculate_checksum(self, file_stream: io.BytesIO) -> str:
        """Genera un hash SHA-256 único del contenido del archivo."""
        # Importante: movemos el 'puntero' al inicio del archivo en RAM
        file_stream.seek(0)
        file_bytes = file_stream.read()
        return hashlib.sha256(file_bytes).hexdigest()