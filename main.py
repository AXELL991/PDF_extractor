import os
from dotenv import load_dotenv

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

# --- Implementaciones (Estructura inicial para empezar con TDD) ---
class PyPDFExtractor(PDFExtractor):
    def extract(self, file_path: str) -> str:
        # TODO: Implementar la lógica real con pypdf
        print(f"[*] Extrayendo texto de: {file_path}")
        return "Texto simulado del PDF."

class OllamaSummarizer(AISummarizer):
    def __init__(self, model_name: str, api_url: str):
        self.model_name = model_name
        self.api_url = api_url

    def summarize(self, text: str) -> str:
        # TODO: Implementar llamada HTTP al modelo o Ollama
        print(f"[*] Resumiendo texto usando {self.model_name} en {self.api_url}...")
        return "Este es un resumen generado por Cerda Santiago."

class MongoDatabase(Database):
    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name

    def save(self, data: dict) -> None:
        # TODO: Implementar inserción real en MongoDB con pymongo
        print(f"[*] Guardando documento en MongoDB ({self.db_name})...")


# --- Flujo principal de la aplicación ---
def main():
    # 12 Factor App: Configuración estricta desde el entorno
    load_dotenv()
    
    # Variables de entorno (YAGNI: Solo traemos lo que necesitamos hoy)
    pdf_target = os.getenv("PDF_FILE_PATH", "documento.pdf")
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name = os.getenv("MONGO_DB_NAME", "pdf_summaries")
    ai_model = os.getenv("AI_MODEL", "llama3")
    ai_api_url = os.getenv("AI_API_URL", "http://localhost:11434/api/generate")

    print("=== Iniciando pdf-extractext ===")

    # Inyección de dependencias
    extractor = PyPDFExtractor()
    summarizer = OllamaSummarizer(model_name=ai_model, api_url=ai_api_url)
    db = MongoDatabase(uri=mongo_uri, db_name=mongo_db_name)

    # Orquestación del proceso
    try:
        # 1. Extracción
        raw_text = extractor.extract(pdf_target)
        
        # 2. Resumen
        summary = summarizer.summarize(raw_text)
        
        # 3. Persistencia
        record = {
            "file_name": pdf_target,
            "original_text_length": len(raw_text),
            "summary": summary
        }
        db.save(record)
        
        print("\n[+] Proceso completado con éxito.")

    except Exception as e:
        print(f"\n[-] Ocurrió un error: {e}")

if __name__ == "__main__":
    main()

print("waacho PUITA")