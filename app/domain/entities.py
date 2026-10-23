"""Entidades puras del dominio, sin dependencias de frameworks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Documento:
    """Documento extraído de un PDF y persistido por el sistema.

    El orden de los campos conserva la compatibilidad posicional con el DTO
    histórico. ``__post_init__`` mantiene las invariantes mínimas del dominio
    sin acoplarse a Pydantic.
    """

    archivo: str
    texto: str = ""
    hash_seguridad: str = ""

    def __post_init__(self) -> None:
        if not self.archivo:
            raise ValueError("El nombre del archivo es obligatorio.")
        if not self.hash_seguridad:
            raise ValueError("El checksum del documento es obligatorio.")
