import os
from dotenv import load_dotenv
import requests


# --- Abstracciones / Interfaces (SOLID: Dependency Inversion Principle) ---
class PDFExtractor:
    def extract(self, file_path: str) -> str:
        raise NotImplementedError


class AISummarizer:
    def summarize(self, text: str) -> str:
        raise NotImplementedError


class Database:
    def save(self, data: dict) -> None:
        raise NotImplementedError


# --- Implementaciones ---
class PyPDFExtractor(PDFExtractor):
    def extract(self, file_path: str) -> str:
        """Extrae texto de un archivo PDF usando pypdf."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            print(f"[!] Error extrayendo PDF: {e}")
            return ""


class OllamaSummarizer(AISummarizer):
    def __init__(self, model_name: str, api_url: str):
        self.model_name = model_name
        self.api_url = api_url

    def summarize(self, text: str) -> str:
        """Genera resumen usando Ollama API local."""
        try:
            prompt = f"Resume el siguiente texto en español:\n\n{text[:4000]}"
            response = requests.post(
                self.api_url,
                json={"model": self.model_name, "prompt": prompt, "stream": False},
                timeout=60,
            )
            response.raise_for_status()
            return response.json().get("response", "No se pudo generar el resumen")
        except Exception as e:
            print(f"[!] Error con Ollama: {e}")
            return f"Error al generar resumen: {e}"


class MoonshotSummarizer(AISummarizer):
    """Summarizer usando la API de Moonshot AI (Kimi K2.5)"""

    def __init__(self, api_key: str, model: str = "moonshotai/kimi-k2.5"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.kimi.moonshot.cn/v1"  # URL de la API de Kimi

    def summarize(self, text: str) -> str:
        """Genera resumen usando Kimi K2.5 API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un asistente experto en resumir documentos de manera clara y concisa.",
                    },
                    {
                        "role": "user",
                        "content": f"Resume el siguiente texto en español:\n\n{text[:8000]}",
                    },
                ],
                "temperature": 0.7,
                "max_tokens": 1000,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.HTTPError as e:
            print(f"[!] Error HTTP de Moonshot: {e}")
            return f"Error en API de Moonshot: {e}"
        except Exception as e:
            print(f"[!] Error general con Moonshot: {e}")
            return f"Error al generar resumen: {e}"


class MongoDatabase(Database):
    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None

    def _connect(self):
        """Conecta a MongoDB lazy loading."""
        if self.client is None:
            from pymongo import MongoClient

            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]

    def save(self, data: dict) -> None:
        """Guarda el documento en MongoDB."""
        try:
            self._connect()
            collection = self.db["summaries"]
            result = collection.insert_one(data)
            print(f"[*] Documento guardado con ID: {result.inserted_id}")
        except Exception as e:
            print(f"[!] Error guardando en MongoDB: {e}")


# --- Flujo principal de la aplicación ---
def main():
    # 12 Factor App: Configuración estricta desde el entorno
    load_dotenv()

    # Variables de entorno
    pdf_target = os.getenv("PDF_FILE_PATH", "documento.pdf")
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name = os.getenv("MONGO_DB_NAME", "pdf_summaries")

    # Configuración de IA
    ai_provider = os.getenv("AI_PROVIDER", "ollama").lower()  # "ollama" o "moonshot"

    # Ollama config
    ai_model = os.getenv("AI_MODEL", "llama3")
    ai_api_url = os.getenv("AI_API_URL", "http://localhost:11434/api/generate")

    # Moonshot config
    moonshot_api_key = os.getenv("MOONSHOT_API_KEY")
    moonshot_model = os.getenv("MOONSHOT_MODEL", "moonshotai/kimi-k2.5")

    print("=== Iniciando pdf-extractext ===")
    print(f"[*] Proveedor de IA: {ai_provider}")

    # Inyección de dependencias
    extractor = PyPDFExtractor()

    # Selección del summarizer según configuración
    if ai_provider == "moonshot":
        if not moonshot_api_key:
            print("[!] ERROR: MOONSHOT_API_KEY no está configurada")
            print("[!] Configura tu API key en el archivo .env")
            return
        summarizer = MoonshotSummarizer(api_key=moonshot_api_key, model=moonshot_model)
    else:
        summarizer = OllamaSummarizer(model_name=ai_model, api_url=ai_api_url)

    db = MongoDatabase(uri=mongo_uri, db_name=mongo_db_name)

    # Orquestación del proceso
    try:
        # 1. Extracción
        print(f"[*] Extrayendo texto de: {pdf_target}")
        raw_text = extractor.extract(pdf_target)

        if not raw_text.strip():
            print("[!] No se pudo extraer texto del PDF")
            return

        print(f"[*] Texto extraído: {len(raw_text)} caracteres")

        # 2. Resumen
        print("[*] Generando resumen...")
        summary = summarizer.summarize(raw_text)

        # 3. Persistencia
        record = {
            "file_name": pdf_target,
            "original_text_length": len(raw_text),
            "text_preview": raw_text[:500],
            "summary": summary,
            "ai_provider": ai_provider,
        }
        db.save(record)

        print("\n[+] Proceso completado con éxito.")
        print(f"[+] Resumen:\n{summary[:500]}...")

    except Exception as e:
        print(f"\n[-] Ocurrió un error: {e}")

if __name__ == "__main__":
    main()
