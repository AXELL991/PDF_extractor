import pytest
from main import PyPDFExtractor, OllamaSummarizer

def test_pypdf_extractor_returns_string():
    # Arrange (Preparar)
    extractor = PyPDFExtractor()
    dummy_path = "dummy.pdf"
    
    # Act (Actuar)
    result = extractor.extract(dummy_path)
    
    # Assert (Afirmar)
    assert isinstance(result, str)
    assert "Texto simulado" in result # Esto pasará con nuestro código actual

def test_ollama_summarizer_formats_correctly():
    # Arrange
    summarizer = OllamaSummarizer(model_name="llama3", api_url="http://localhost")
    input_text = "Texto muy largo que necesita ser resumido."
    
    # Act
    summary = summarizer.summarize(input_text)
    
    # Assert
    assert isinstance(summary, str)
    assert len(summary) > 0