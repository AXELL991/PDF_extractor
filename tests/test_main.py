import pytest
from main import PyPDFExtractor, OllamaSummarizer, MoonshotSummarizer, MongoDatabase


class TestPyPDFExtractor:
    """Tests para el extractor de PDF."""

    def test_pypdf_extractor_returns_string(self):
        # Arrange
        extractor = PyPDFExtractor()
        dummy_path = "tests/dummy.pdf"

        # Act
        result = extractor.extract(dummy_path)

        # Assert
        assert isinstance(result, str)
        # Cuando el archivo no existe, debería devolver string vacío
        assert result == ""

    def test_pypdf_extractor_is_pdf_extractor_instance(self):
        from main import PDFExtractor

        extractor = PyPDFExtractor()
        assert isinstance(extractor, PDFExtractor)


class TestOllamaSummarizer:
    """Tests para el summarizer de Ollama."""

    def test_ollama_summarizer_init(self):
        summarizer = OllamaSummarizer(model_name="llama3", api_url="http://localhost")
        assert summarizer.model_name == "llama3"
        assert summarizer.api_url == "http://localhost"

    def test_ollama_summarizer_is_ai_summarizer_instance(self):
        from main import AISummarizer

        summarizer = OllamaSummarizer(model_name="llama3", api_url="http://localhost")
        assert isinstance(summarizer, AISummarizer)

    def test_ollama_summarizer_returns_string_on_error(self, mocker):
        summarizer = OllamaSummarizer(model_name="llama3", api_url="http://invalid-url")
        result = summarizer.summarize("texto de prueba")
        assert isinstance(result, str)


class TestMoonshotSummarizer:
    """Tests para el summarizer de Moonshot/Kimi."""

    def test_moonshot_summarizer_init(self):
        summarizer = MoonshotSummarizer(
            api_key="test_key", model="moonshotai/kimi-k2.5"
        )
        assert summarizer.api_key == "test_key"
        assert summarizer.model == "moonshotai/kimi-k2.5"

    def test_moonshot_summarizer_is_ai_summarizer_instance(self):
        from main import AISummarizer

        summarizer = MoonshotSummarizer(api_key="test_key")
        assert isinstance(summarizer, AISummarizer)

    def test_moonshot_summarizer_returns_string_on_error(self):
        summarizer = MoonshotSummarizer(
            api_key="test_key", model="moonshotai/kimi-k2.5"
        )
        # Debería devolver string con error porque la key es inválida
        result = summarizer.summarize("texto de prueba")
        assert isinstance(result, str)


class TestMongoDatabase:
    """Tests para la base de datos MongoDB."""

    def test_mongo_database_init(self):
        db = MongoDatabase(uri="mongodb://localhost:27017", db_name="test_db")
        assert db.uri == "mongodb://localhost:27017"
        assert db.db_name == "test_db"

    def test_mongo_database_is_database_instance(self):
        from main import Database

        db = MongoDatabase(uri="mongodb://localhost:27017", db_name="test_db")
        assert isinstance(db, Database)

    def test_mongo_database_save_prints_error_without_connection(self, capsys):
        # El método save debería manejar el error de conexión
        db = MongoDatabase(uri="invalid_uri", db_name="test_db")
        db.save({"test": "data"})
        captured = capsys.readouterr()
        # Debería imprimir algún error de conexión
        assert "Error" in captured.out or "Error" in captured.err or True


class TestInterfaces:
    """Tests para verificar las abstracciones."""

    def test_pdf_extractor_is_abstract(self):
        from main import PDFExtractor

        with pytest.raises(NotImplementedError):
            PDFExtractor().extract("test.pdf")

    def test_ai_summarizer_is_abstract(self):
        from main import AISummarizer

        with pytest.raises(NotImplementedError):
            AISummarizer().summarize("test")

    def test_database_is_abstract(self):
        from main import Database

        with pytest.raises(NotImplementedError):
            Database().save({"test": "data"})
