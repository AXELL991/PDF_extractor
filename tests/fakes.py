"""Fakes compartidos por los tests de casos de uso y de contrato HTTP."""

from dataclasses import replace

from app.domain.entities import Documento
from app.main import create_app


class FakeRepo:
    """Repositorio en memoria que registra llamadas y respeta el contrato real."""

    def __init__(self, documentos: list[Documento] | None = None, ping_error=None):
        self.documentos = {doc.hash_seguridad: doc for doc in documentos or []}
        self.llamadas: list[tuple] = []
        self.ping_error = ping_error
        self.guardado: Documento | None = None

    def obtener_por_checksum(self, checksum: str) -> Documento | None:
        self.llamadas.append(("obtener_por_checksum", checksum))
        return self.documentos.get(checksum)

    def guardar_documento(self, documento: Documento) -> None:
        self.llamadas.append(("guardar_documento", documento.hash_seguridad))
        self.guardado = documento
        self.documentos[documento.hash_seguridad] = documento

    def listar_todos(self) -> list[Documento]:
        self.llamadas.append(("listar_todos",))
        return list(self.documentos.values())

    def actualizar_nombre(self, checksum: str, nuevo_nombre: str) -> None:
        self.llamadas.append(("actualizar_nombre", checksum, nuevo_nombre))
        documento = self.documentos.get(checksum)
        if documento is not None:
            self.documentos[checksum] = replace(documento, archivo=nuevo_nombre)

    def eliminar_documento(self, checksum: str) -> None:
        self.llamadas.append(("eliminar_documento", checksum))
        self.documentos.pop(checksum, None)

    def ping(self) -> None:
        self.llamadas.append(("ping",))
        if self.ping_error is not None:
            raise self.ping_error


class FakeExtractor:
    """Extractor controlable que registra el orden de sus operaciones."""

    def __init__(
        self,
        texto: str = "Texto extraído",
        llamadas: list[tuple] | None = None,
    ):
        self.texto = texto
        self.llamadas = llamadas if llamadas is not None else []

    def extract(self, file_stream) -> str:
        self.llamadas.append(("extraer",))
        return self.texto


class FakeChecksumCalculator:
    """Calculador de checksum controlable para tests de aplicación."""

    def __init__(
        self,
        checksum: str = "a" * 64,
        llamadas: list[tuple] | None = None,
    ):
        self.checksum = checksum
        self.llamadas = llamadas if llamadas is not None else []

    def calculate(self, content: bytes) -> str:
        self.llamadas.append(("calcular_checksum",))
        return self.checksum


def build_test_app(
    repositorio: FakeRepo,
    extractor=None,
    checksum_calculator=None,
):
    """Monta la app real con dependencias de test inyectadas por la factory."""
    test_app = create_app(repositorio=repositorio, extractor=extractor)
    if checksum_calculator is not None:
        test_app.state.checksum_calculator = checksum_calculator
    return test_app
