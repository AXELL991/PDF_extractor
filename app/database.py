import os

from dotenv import load_dotenv
from pymongo import MongoClient

from app.dtos import Documento

load_dotenv()


class MongoRepository:
    """Adaptador de persistencia: traduce entre MongoDB y el dominio."""

    def __init__(self):
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGO_DB_NAME", "pdf_extractor_db")

        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.coleccion = self.db["documentos"]

    def obtener_por_checksum(self, checksum: str) -> Documento | None:
        """Busca un documento por su hash y lo devuelve como entidad de dominio."""
        doc = self.coleccion.find_one({"hash_seguridad": checksum})
        return Documento.model_validate(doc) if doc else None

    def guardar_documento(self, documento: Documento) -> None:
        """Persiste una entidad de dominio en la colección."""
        self.coleccion.insert_one(documento.model_dump())

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
        return [Documento.model_validate(doc) for doc in self.coleccion.find({})]

    def ping(self) -> None:
        """Comprueba la conectividad con MongoDB."""
        self.client.admin.command("ping")
