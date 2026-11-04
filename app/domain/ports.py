"""Contratos (puertos) de salida del dominio.

Define las abstracciones que la capa de aplicación requiere para
persistir, extraer y calcular checksums, sin acoplarse a implementaciones
concretas de infraestructura.
"""

from typing import Protocol

from app.domain.entities import Documento


class DocumentRepositoryABC(Protocol):
    """Contrato de persistencia para documentos."""

    def obtener_por_checksum(self, checksum: str) -> Documento | None: ...
    def guardar_documento(self, documento: Documento) -> None: ...
    def listar_todos(self) -> list[Documento]: ...
    def actualizar_nombre(self, checksum: str, nuevo_nombre: str) -> None: ...
    def eliminar_documento(self, checksum: str) -> None: ...
    def ping(self) -> None: ...
