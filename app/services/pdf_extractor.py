import hashlib
import io
import logging
import re
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PyPDFExtractor:
    """Clase encargada de la lógica de negocio: extraer contenido en Markdown y generar hash."""

    def extract(self, file_stream: io.BytesIO) -> str:
        """Recibe un flujo de bytes en RAM y devuelve el contenido del PDF formateado en Markdown."""
        try:
            reader = PdfReader(file_stream)
            markdown_pages = []

            for index, page in enumerate(reader.pages, start=1):
                raw_text = page.extract_text() or ""
                page_markdown = self._format_page_to_markdown(raw_text, index)
                if page_markdown:
                    markdown_pages.append(page_markdown)

            return "\n\n---\n\n".join(markdown_pages).strip()
        except Exception as e:
            logger.error(f"Error en la extracción a Markdown: {e}", exc_info=True)
            return ""

    def _format_page_to_markdown(self, text: str, page_number: int) -> str:
        """Convierte el texto de una página a estructura Markdown limpia."""
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line]

        if not lines:
            return ""

        formatted_lines = [f"## Página {page_number}"]

        for line in lines:
            # Títulos o subtítulos en mayúsculas o que terminen en dos puntos
            if len(line) < 60 and (line.isupper() or line.endswith(":")):
                formatted_lines.append(f"### {line.rstrip(':')}")
            # Si ya tiene viñeta o numeración
            elif re.match(r"^(\*|-|\d+\.)\s+", line):
                formatted_lines.append(line)
            else:
                formatted_lines.append(line)

        return "\n\n".join(formatted_lines)

    def calculate_checksum(self, file_stream: io.BytesIO) -> str:
        """Genera un hash SHA-256 único del contenido del archivo."""
        file_stream.seek(0)
        file_bytes = file_stream.read()
        return hashlib.sha256(file_bytes).hexdigest()
