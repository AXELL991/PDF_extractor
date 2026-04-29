import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class MongoRepository:
    def __init__(self):
        # Usamos los nombres exactos de tu .env
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGO_DB_NAME", "pdf_extractor_db")
        
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.coleccion = self.db["documentos"]

    def obtener_por_checksum(self, checksum: str):
        """Busca un documento por su hash."""
        return self.coleccion.find_one({"hash_seguridad": checksum})

    def guardar_documento(self, nombre: str, texto: str, checksum: str):
        """Guarda el texto y el hash en la NoSQL."""
        documento = {
            "archivo": nombre,
            "texto": texto,
            "hash_seguridad": checksum
        }
        return self.coleccion.insert_one(documento)

    def actualizar_nombre(self, checksum: str, nuevo_nombre: str):
        """Actualiza el nombre de un documento."""
        return self.coleccion.update_one(
            {"hash_seguridad": checksum},
            {"$set": {"archivo": nuevo_nombre}}
        )

    def eliminar_documento(self, checksum: str):
        """Elimina un documento por su hash."""
        return self.coleccion.delete_one({"hash_seguridad": checksum})

    def existe_documento(self, checksum: str) -> bool:
        """Verifica si existe un documento con el hash dado."""
        return self.coleccion.find_one({"hash_seguridad": checksum}) is not None

    def listar_todos(self):
        """Para el CRUD: lista todos los documentos."""
        return list(self.coleccion.find({}, {"_id": 0})) # El 0 oculta el ID feo de Mongo