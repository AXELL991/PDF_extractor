from dataclasses import asdict

from pymongo import MongoClient

from app.core.config import MONGO_DB_NAME, MONGO_URI
from app.domain.entities import Documento


def _a_documento(doc: dict) -> Documento:
    """Traduce un documento de MongoDB a la entidad pura de dominio."""
    return Documento(
        archivo=doc["archivo"],
        texto=doc.get("texto", ""),
        hash_seguridad=doc["hash_seguridad"],
    )


class MongoRepository:
    """Adaptador de persistencia: traduce entre MongoDB y el dominio."""

    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB_NAME]
        self.coleccion = self.db["documentos"]

    def obtener_por_checksum(self, checksum: str) -> Documento | None:
        """Busca un documento por su hash y lo devuelve como entidad de dominio."""
        doc = self.coleccion.find_one({"hash_seguridad": checksum})
        return _a_documento(doc) if doc else None

    def guardar_documento(self, documento: Documento) -> None:
        """Persiste una entidad de dominio en la colección."""
        self.coleccion.insert_one(asdict(documento))

    def actualizar_nombre(self, checksum: str, nuevo_nombre: str) -> None:
        """Actualiza el nombre de un documento."""
        self.coleccion.update_one(
            {"hash_seguridad": checksum},
            {"$set": {"archivo": nuevo_nombre}},
        )

    def eliminar_documento(self, checksum: str) -> None:
        """Elimina un documento por su hash."""
        self.coleccion.delete_one({"hash_seguridad": checksum})

    def listar_todos(self) -> list[Documento]:
        """Devuelve todos los documentos como entidades de dominio."""
        return [_a_documento(doc) for doc in self.coleccion.find({})]

    def ping(self) -> None:
        """Comprueba la conectividad con MongoDB."""
        self.client.admin.command("ping")
