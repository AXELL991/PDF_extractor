"""Configuración centralizada de la aplicación, leída del entorno.

Utiliza ``pydantic-settings`` (Factor III de 12-Factor App) para leer todas
las variables desde el entorno o el archivo ``.env``, sin hardcodear
credenciales en el código.

La configuración se obtiene mediante ``get_settings()`` (con ``@lru_cache``)
para evitar instanciación con efectos secundarios al importar el módulo.
"""

from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación con valores por defecto y override vía entorno."""

    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"

    # Configuración de base de datos
    MONGO_URI: str = Field(default="mongodb://localhost:27017")
    MONGO_DB_NAME: str = Field(default="pdf_extractor_db")

    # Configuración de tamaño de archivo (única fuente de verdad)
    MAX_FILE_SIZE_MB: int = Field(default=5)

    # Orígenes CORS permitidos (solo los configurados explícitamente)
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8080,https://pdf-extractor.utn.edu.ar"
    )

    # Hosts válidos para el header Host (evita Host header injection)
    ALLOWED_HOSTS: str = Field(
        default="localhost,127.0.0.1,traefik,pdf-extractor-api,*.utn.edu.ar,pdf-extractor.utn.edu.ar"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("MONGO_URI")
    @classmethod
    def _validar_mongo_uri(cls, value: str) -> str:
        if not value or not value.startswith("mongodb://"):
            raise ValueError("MONGO_URI debe ser una URI de MongoDB válida.")
        return value

    @field_validator("MONGO_DB_NAME")
    @classmethod
    def _validar_mongo_db_name(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("MONGO_DB_NAME no puede estar vacío.")
        return value

    @field_validator("MAX_FILE_SIZE_MB")
    @classmethod
    def _validar_max_file_size_mb(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("MAX_FILE_SIZE_MB debe ser un entero positivo.")
        return value

    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]

    def validate(self) -> None:
        """Valida la configuración que debe fallar rápido al arrancar."""
        # Los field_validators ya cubren las validaciones críticas.
        # Este método se mantiene para compatibilidad y validaciones cruzadas futuras.
        pass


@lru_cache()
def get_settings() -> Settings:
    """Devuelve la configuración cacheada (sin efectos secundarios en import)."""
    return Settings()


def validate_config() -> None:
    """Valida la configuración cargada. Debe llamarse explícitamente al arrancar."""
    get_settings().validate()
