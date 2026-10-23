"""Tests unitarios directos de los casos de uso, sin infraestructura HTTP."""

import pytest

from app.core.config import MAX_FILE_SIZE_BYTES
from app.dtos import Documento
from app.exceptions import (
    ChecksumInvalidoError,
    DocumentoDuplicadoError,
    DocumentoNoEncontradoError,
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
from app.use_cases.procesar_documento import ProcesarDocumentoUseCase
from tests.fakes import FakeExtractor, FakeRepo


CHECKSUM = "a" * 64
OTRO_CHECKSUM = "b" * 64


def documento(archivo: str = "documento.pdf", checksum: str = CHECKSUM) -> Documento:
    return Documento(archivo=archivo, texto="contenido", hash_seguridad=checksum)


class TestProcesarDocumentoUseCase:
    """Verifica la orquestación completa del upload y sus efectos secundarios."""

    def test_exito_registra_orden_y_persiste(self, pdf_con_texto):
        repo = FakeRepo()
        extractor = FakeExtractor(
            checksum=CHECKSUM,
            texto="Hola PDF",
            llamadas=repo.llamadas,
        )
        use_case = ProcesarDocumentoUseCase(extractor=extractor, db=repo)

        respuesta = use_case.execute("test.pdf", pdf_con_texto)

        assert respuesta.sha256 == CHECKSUM
        assert respuesta.filename == "test.pdf"
        assert repo.guardado == Documento(
            archivo="test.pdf",
            texto="Hola PDF",
            hash_seguridad=CHECKSUM,
        )
        assert repo.llamadas == [
            ("calcular_checksum",),
            ("obtener_por_checksum", CHECKSUM),
            ("extraer",),
            ("guardar_documento", CHECKSUM),
        ]

    def test_sanitiza_texto_extraido(self, pdf_con_texto):
        repo = FakeRepo()
        extractor = FakeExtractor(
            checksum=CHECKSUM,
            texto="<script>alert('xss')</script>Hola <b>mundo</b>",
            llamadas=repo.llamadas,
        )
        use_case = ProcesarDocumentoUseCase(extractor=extractor, db=repo)

        use_case.execute("test.pdf", pdf_con_texto)

        assert repo.guardado is not None
        assert "<script>" not in repo.guardado.texto
        assert "<b>" not in repo.guardado.texto
        assert "Hola" in repo.guardado.texto
        assert "mundo" in repo.guardado.texto

    def test_duplicado_no_extrae_ni_guarda(self, pdf_con_texto):
        repo = FakeRepo([documento(checksum=CHECKSUM)])
        extractor = FakeExtractor(checksum=CHECKSUM, llamadas=repo.llamadas)
        use_case = ProcesarDocumentoUseCase(extractor=extractor, db=repo)

        with pytest.raises(DocumentoDuplicadoError):
            use_case.execute("test.pdf", pdf_con_texto)

        assert repo.guardado is None
        assert repo.llamadas == [
            ("calcular_checksum",),
            ("obtener_por_checksum", CHECKSUM),
        ]

    def test_archivo_excedido_no_toca_dependencias(self, pdf_con_texto):
        repo = FakeRepo()
        extractor = FakeExtractor(llamadas=repo.llamadas)
        use_case = ProcesarDocumentoUseCase(extractor=extractor, db=repo)

        with pytest.raises(TamañoExcedidoError):
            use_case.execute(
                "test.pdf",
                pdf_con_texto,
                file_size=MAX_FILE_SIZE_BYTES + 1,
            )

        assert repo.llamadas == []
        assert extractor.llamadas == []
        assert repo.guardado is None

    def test_pdf_corrupto_no_toca_dependencias(self):
        repo = FakeRepo()
        extractor = FakeExtractor(llamadas=repo.llamadas)
        use_case = ProcesarDocumentoUseCase(extractor=extractor, db=repo)

        with pytest.raises(FormatoInvalidoError):
            use_case.execute("test.pdf", b"%PDF-1.4 contenido corrupto")

        assert repo.llamadas == []
        assert extractor.llamadas == []
        assert repo.guardado is None

    def test_nombre_invalido_no_toca_dependencias(self, pdf_con_texto):
        repo = FakeRepo()
        extractor = FakeExtractor(llamadas=repo.llamadas)
        use_case = ProcesarDocumentoUseCase(extractor=extractor, db=repo)

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

        resultado = ObtenerDocumentoUseCase(repo).execute(CHECKSUM)

        assert resultado == doc
        assert repo.llamadas == [("obtener_por_checksum", CHECKSUM)]

    def test_checksum_invalido_no_consulta_repositorio(self):
        repo = FakeRepo()

        with pytest.raises(ChecksumInvalidoError):
            ObtenerDocumentoUseCase(repo).execute("123")

        assert repo.llamadas == []

    def test_documento_no_encontrado(self):
        repo = FakeRepo()

        with pytest.raises(DocumentoNoEncontradoError):
            ObtenerDocumentoUseCase(repo).execute(OTRO_CHECKSUM)

        assert repo.llamadas == [("obtener_por_checksum", OTRO_CHECKSUM)]


class TestActualizarDocumentoUseCase:
    def test_actualiza_y_sanitiza_nombre(self):
        repo = FakeRepo([documento("viejo.pdf")])
        use_case = ActualizarDocumentoUseCase(repo)

        resultado = use_case.execute(CHECKSUM, "../nuevo.pdf")

        assert resultado == "nuevo.pdf"
        assert repo.documentos[CHECKSUM].archivo == "nuevo.pdf"
        assert repo.llamadas == [
            ("obtener_por_checksum", CHECKSUM),
            ("actualizar_nombre", CHECKSUM, "nuevo.pdf"),
        ]

    def test_checksum_invalido_no_actualiza(self):
        repo = FakeRepo([documento()])

        with pytest.raises(ChecksumInvalidoError):
            ActualizarDocumentoUseCase(repo).execute("123", "nuevo.pdf")

        assert repo.llamadas == []

    def test_documento_no_encontrado_no_actualiza(self):
        repo = FakeRepo()

        with pytest.raises(DocumentoNoEncontradoError):
            ActualizarDocumentoUseCase(repo).execute(OTRO_CHECKSUM, "nuevo.pdf")

        assert repo.llamadas == [("obtener_por_checksum", OTRO_CHECKSUM)]

    def test_nombre_invalido_no_actualiza(self):
        repo = FakeRepo([documento()])

        with pytest.raises(NombreArchivoInvalidoError):
            ActualizarDocumentoUseCase(repo).execute(CHECKSUM, "archivo.exe")

        assert repo.llamadas == [("obtener_por_checksum", CHECKSUM)]


class TestEliminarDocumentoUseCase:
    def test_elimina_documento_existente(self):
        repo = FakeRepo([documento()])
        use_case = EliminarDocumentoUseCase(repo)

        use_case.execute(CHECKSUM)

        assert CHECKSUM not in repo.documentos
        assert repo.llamadas == [
            ("obtener_por_checksum", CHECKSUM),
            ("eliminar_documento", CHECKSUM),
        ]

    def test_checksum_invalido_no_elimina(self):
        repo = FakeRepo([documento()])

        with pytest.raises(ChecksumInvalidoError):
            EliminarDocumentoUseCase(repo).execute("123")

        assert repo.llamadas == []

    def test_documento_no_encontrado_no_elimina(self):
        repo = FakeRepo()

        with pytest.raises(DocumentoNoEncontradoError):
            EliminarDocumentoUseCase(repo).execute(OTRO_CHECKSUM)

        assert repo.llamadas == [("obtener_por_checksum", OTRO_CHECKSUM)]
