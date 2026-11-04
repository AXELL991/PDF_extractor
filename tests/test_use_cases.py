"""Tests unitarios directos de los casos de uso, sin infraestructura HTTP."""

from dataclasses import FrozenInstanceError

import pytest

from app.core.config import get_settings
from app.core.security.service import SecurityService
from app.domain.entities import Documento
from app.domain.exceptions import (
    ChecksumInvalidoError,
    DocumentoDuplicadoError,
    DocumentoNoEncontradoError,
    ExtractionError,
    FormatoInvalidoError,
    NombreArchivoInvalidoError,
    TamañoExcedidoError,
)
from app.use_cases.gestionar_documentos import (
    ActualizarDocumentoUseCase,
    EliminarDocumentoUseCase,
    ListarDocumentosUseCase,
    ObtenerDocumentoUseCase,
)
from app.use_cases.procesar_documento import (
    ProcesarDocumentoUseCase,
    ResultadoDocumento,
)
from tests.fakes import (
    FakeChecksumCalculator,
    FakeExtractor,
    FakeRepo,
    FakeSanitization,
)

settings = get_settings()
MAX_FILE_SIZE_BYTES = settings.MAX_FILE_SIZE_BYTES
REAL_SANITIZATION = SecurityService()

CHECKSUM = "a" * 64
OTRO_CHECKSUM = "b" * 64


def documento(archivo: str = "documento.pdf", checksum: str = CHECKSUM) -> Documento:
    return Documento(archivo=archivo, texto="contenido", hash_seguridad=checksum)


def test_resultado_documento_es_inmutable():
    resultado = ResultadoDocumento(filename="test.pdf", sha256=CHECKSUM)

    with pytest.raises(FrozenInstanceError):
        resultado.filename = "otro.pdf"


def test_resultado_documento_igualdad_por_valor():
    assert ResultadoDocumento("test.pdf", CHECKSUM) == ResultadoDocumento(
        "test.pdf", CHECKSUM
    )


def _use_case(repo, extractor=None, sanitization=None, checksum=CHECKSUM):
    extractor = extractor or FakeExtractor(llamadas=repo.llamadas)
    calculador = FakeChecksumCalculator(
        checksum=checksum,
        llamadas=repo.llamadas,
    )
    sanitization = sanitization or FakeSanitization(llamadas=repo.llamadas)
    return ProcesarDocumentoUseCase(
        extractor=extractor,
        db=repo,
        checksum_calculator=calculador,
        sanitization=sanitization,
        max_size_bytes=MAX_FILE_SIZE_BYTES,
    )


class TestProcesarDocumentoUseCase:
    """Verifica la orquestación completa del upload y sus efectos secundarios."""

    def test_exito_registra_orden_y_persiste(self, pdf_con_texto):
        repo = FakeRepo()
        extractor = FakeExtractor(texto="Hola PDF", llamadas=repo.llamadas)
        use_case = _use_case(repo, extractor)

        respuesta = use_case.execute("test.pdf", pdf_con_texto)

        assert isinstance(respuesta, ResultadoDocumento)
        assert respuesta.sha256 == CHECKSUM
        assert respuesta.filename == "test.pdf"
        assert repo.guardado == Documento(
            archivo="test.pdf",
            texto="Hola PDF",
            hash_seguridad=CHECKSUM,
        )
        assert repo.llamadas == [
            ("sanitize_filename", "test.pdf"),
            ("validate_pdf",),
            ("calcular_checksum",),
            ("obtener_por_checksum", CHECKSUM),
            ("extraer",),
            ("sanitize_text", "Hola PDF"),
            ("guardar_documento", CHECKSUM),
        ]

    def test_sanitiza_texto_extraido(self, pdf_con_texto):
        repo = FakeRepo()
        extractor = FakeExtractor(
            texto="<script>alert('xss')</script>Hola <b>mundo</b>",
            llamadas=repo.llamadas,
        )
        use_case = _use_case(repo, extractor, sanitization=REAL_SANITIZATION)

        use_case.execute("test.pdf", pdf_con_texto)

        assert repo.guardado is not None
        assert "<script>" not in repo.guardado.texto
        assert "<b>" not in repo.guardado.texto
        assert "Hola" in repo.guardado.texto
        assert "mundo" in repo.guardado.texto

    def test_pdf_sin_texto_persiste_constante(self, pdf_con_texto):
        repo = FakeRepo()
        extractor = FakeExtractor(texto="", llamadas=repo.llamadas)
        use_case = _use_case(repo, extractor)

        use_case.execute("test.pdf", pdf_con_texto)

        assert repo.guardado is not None
        assert repo.guardado.texto == "Vacio"

    def test_error_de_extraccion_no_persiste(self, pdf_con_texto):
        class ExtractorRoto:
            def extract(self, file_stream) -> str:
                raise ExtractionError()

        repo = FakeRepo()
        use_case = _use_case(repo, ExtractorRoto())

        with pytest.raises(ExtractionError):
            use_case.execute("test.pdf", pdf_con_texto)

        assert repo.guardado is None

    def test_duplicado_no_extrae_ni_guarda(self, pdf_con_texto):
        repo = FakeRepo([documento(checksum=CHECKSUM)])
        use_case = _use_case(repo)

        with pytest.raises(DocumentoDuplicadoError):
            use_case.execute("test.pdf", pdf_con_texto)

        assert repo.guardado is None
        assert repo.llamadas == [
            ("sanitize_filename", "test.pdf"),
            ("validate_pdf",),
            ("calcular_checksum",),
            ("obtener_por_checksum", CHECKSUM),
        ]

    def test_archivo_excedido_no_toca_dependencias(self, pdf_con_texto):
        repo = FakeRepo()
        extractor = FakeExtractor(llamadas=repo.llamadas)
        use_case = _use_case(repo, extractor)

        with pytest.raises(TamañoExcedidoError):
            use_case.execute(
                "test.pdf",
                pdf_con_texto,
                file_size=MAX_FILE_SIZE_BYTES + 1,
            )

        assert repo.llamadas == []
        assert extractor.llamadas == []
        assert repo.guardado is None

    def test_archivo_excedido_sin_file_size_usa_len_de_content_bytes(self):
        """Cuando file_size es None, el caso de uso calcula len(content_bytes)."""
        repo = FakeRepo()
        extractor = FakeExtractor(llamadas=repo.llamadas)
        use_case = _use_case(repo, extractor)

        contenido_grande = b"x" * (MAX_FILE_SIZE_BYTES + 1)

        with pytest.raises(TamañoExcedidoError):
            use_case.execute("test.pdf", contenido_grande, file_size=None)

        assert repo.llamadas == []
        assert extractor.llamadas == []
        assert repo.guardado is None

    def test_archivo_en_limite_exacto_es_aceptado(self, pdf_con_texto):
        """Archivo exactamente en el límite de 5MB debe ser aceptado."""
        repo = FakeRepo()
        extractor = FakeExtractor(texto="ok", llamadas=repo.llamadas)
        use_case = _use_case(repo, extractor)

        contenido_limite = b"x" * MAX_FILE_SIZE_BYTES
        respuesta = use_case.execute(
            "test.pdf", contenido_limite, file_size=MAX_FILE_SIZE_BYTES
        )
        assert respuesta is not None

    def test_nombre_con_espacios_y_puntos_multiples(self, pdf_con_texto):
        """Nombres con espacios y múltiples puntos deben ser aceptados."""
        repo = FakeRepo()
        extractor = FakeExtractor(texto="ok", llamadas=repo.llamadas)
        use_case = _use_case(repo, extractor, sanitization=REAL_SANITIZATION)

        respuesta = use_case.execute("my.document.v2.pdf", pdf_con_texto)

        assert respuesta.filename == "my.document.v2.pdf"

    def test_archivo_vacio_de_cero_bytes(self, pdf_con_texto):
        """Archivo de 0 bytes debe ser rechazado por validación de PDF."""
        repo = FakeRepo()
        extractor = FakeExtractor(llamadas=repo.llamadas)
        sanitization = FakeSanitization(
            validate_pdf_result=False, llamadas=repo.llamadas
        )
        use_case = _use_case(repo, extractor, sanitization)

        with pytest.raises(FormatoInvalidoError):
            use_case.execute("vacio.pdf", b"")

        assert repo.guardado is None

    def test_pdf_corrupto_no_toca_dependencias(self):
        repo = FakeRepo()
        extractor = FakeExtractor()
        sanitization = FakeSanitization(
            validate_pdf_result=False, llamadas=repo.llamadas
        )
        use_case = _use_case(repo, extractor, sanitization)

        with pytest.raises(FormatoInvalidoError):
            use_case.execute("test.pdf", b"%PDF-1.4 contenido corrupto")

        assert repo.llamadas == [
            ("sanitize_filename", "test.pdf"),
            ("validate_pdf",),
        ]
        assert extractor.llamadas == []
        assert repo.guardado is None

    def test_nombre_invalido_no_toca_dependencias(self, pdf_con_texto):
        repo = FakeRepo()
        extractor = FakeExtractor(llamadas=repo.llamadas)
        sanitization = FakeSanitization(llamadas=repo.llamadas)
        sanitization.sanitize_filename = lambda _: (_ for _ in ()).throw(
            ValueError("Nombre inválido")
        )
        use_case = _use_case(repo, extractor, sanitization)

        with pytest.raises(NombreArchivoInvalidoError):
            use_case.execute("test.txt", pdf_con_texto)

        assert repo.llamadas == []
        assert extractor.llamadas == []
        assert repo.guardado is None


class TestListarDocumentosUseCase:
    def test_devuelve_todos_y_registra_llamada(self):
        docs = [documento("uno.pdf", CHECKSUM), documento("dos.pdf", OTRO_CHECKSUM)]
        repo = FakeRepo(docs)

        resultado = ListarDocumentosUseCase(repo).execute()

        assert resultado == docs
        assert repo.llamadas == [("listar_todos",)]


class TestObtenerDocumentoUseCase:
    def test_devuelve_documento_existente(self):
        doc = documento()
        repo = FakeRepo([doc])
        sanitization = REAL_SANITIZATION

        resultado = ObtenerDocumentoUseCase(repo, sanitization).execute(CHECKSUM)

        assert resultado == doc
        assert repo.llamadas == [("obtener_por_checksum", CHECKSUM)]

    def test_checksum_invalido_no_consulta_repositorio(self):
        repo = FakeRepo()
        sanitization = FakeSanitization()
        sanitization.validate_checksum = lambda _: (_ for _ in ()).throw(
            ValueError("Checksum inválido")
        )

        with pytest.raises(ChecksumInvalidoError):
            ObtenerDocumentoUseCase(repo, sanitization).execute("123")

        assert repo.llamadas == []

    def test_documento_no_encontrado(self):
        repo = FakeRepo()
        sanitization = REAL_SANITIZATION

        with pytest.raises(DocumentoNoEncontradoError):
            ObtenerDocumentoUseCase(repo, sanitization).execute(OTRO_CHECKSUM)

        assert repo.llamadas == [("obtener_por_checksum", OTRO_CHECKSUM)]


class TestActualizarDocumentoUseCase:
    def test_actualiza_y_sanitiza_nombre(self):
        repo = FakeRepo([documento("viejo.pdf")])
        sanitization = REAL_SANITIZATION
        use_case = ActualizarDocumentoUseCase(repo, sanitization)

        resultado = use_case.execute(CHECKSUM, "../nuevo.pdf")

        assert resultado == "nuevo.pdf"
        assert repo.documentos[CHECKSUM].archivo == "nuevo.pdf"
        assert repo.llamadas == [
            ("obtener_por_checksum", CHECKSUM),
            ("actualizar_nombre", CHECKSUM, "nuevo.pdf"),
        ]

    def test_checksum_invalido_no_actualiza(self):
        repo = FakeRepo([documento()])
        sanitization = FakeSanitization()
        sanitization.validate_checksum = lambda _: (_ for _ in ()).throw(
            ValueError("Checksum inválido")
        )

        with pytest.raises(ChecksumInvalidoError):
            ActualizarDocumentoUseCase(repo, sanitization).execute("123", "nuevo.pdf")

        assert repo.llamadas == []

    def test_documento_no_encontrado_no_actualiza(self):
        repo = FakeRepo()
        sanitization = REAL_SANITIZATION

        with pytest.raises(DocumentoNoEncontradoError):
            ActualizarDocumentoUseCase(repo, sanitization).execute(
                OTRO_CHECKSUM, "nuevo.pdf"
            )

        assert repo.llamadas == [("obtener_por_checksum", OTRO_CHECKSUM)]

    def test_nombre_invalido_no_actualiza(self):
        repo = FakeRepo([documento()])
        sanitization = FakeSanitization()
        sanitization.sanitize_filename = lambda _: (_ for _ in ()).throw(
            ValueError("Nombre inválido")
        )

        with pytest.raises(NombreArchivoInvalidoError):
            ActualizarDocumentoUseCase(repo, sanitization).execute(
                CHECKSUM, "archivo.exe"
            )

        assert repo.llamadas == [("obtener_por_checksum", CHECKSUM)]


class TestEliminarDocumentoUseCase:
    def test_elimina_documento_existente(self):
        repo = FakeRepo([documento()])
        sanitization = REAL_SANITIZATION
        use_case = EliminarDocumentoUseCase(repo, sanitization)

        use_case.execute(CHECKSUM)

        assert CHECKSUM not in repo.documentos
        assert repo.llamadas == [
            ("obtener_por_checksum", CHECKSUM),
            ("eliminar_documento", CHECKSUM),
        ]

    def test_checksum_invalido_no_elimina(self):
        repo = FakeRepo([documento()])
        sanitization = FakeSanitization()
        sanitization.validate_checksum = lambda _: (_ for _ in ()).throw(
            ValueError("Checksum inválido")
        )

        with pytest.raises(ChecksumInvalidoError):
            EliminarDocumentoUseCase(repo, sanitization).execute("123")

        assert repo.llamadas == []

    def test_documento_no_encontrado_no_elimina(self):
        repo = FakeRepo()
        sanitization = REAL_SANITIZATION

        with pytest.raises(DocumentoNoEncontradoError):
            EliminarDocumentoUseCase(repo, sanitization).execute(OTRO_CHECKSUM)

        assert repo.llamadas == [("obtener_por_checksum", OTRO_CHECKSUM)]
