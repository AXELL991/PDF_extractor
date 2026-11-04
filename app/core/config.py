"""Configuración centralizada de la aplicación, leída del entorno.

Utiliza ``pydantic-settings`` (Factor III de 12-Factor App) para leer todas
las variables desde el entorno o el archivo ``.env``, sin hardcodear
credenciales en el código.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación con valores por defecto y override vía entorno."""

    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"

    # Configuración de base de datos
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "pdf_extractor_db"

    # Configuración de tamaño de archivo (única fuente de verdad)
    MAX_FILE_SIZE_MB: int = 5

    # Orígenes CORS permitidos (solo los configurados explícitamente)
    ALLOWED_ORIGINS: str = (
        "http://localhost:3000,http://localhost:8080,https://pdf-extractor.utn.edu.ar"
    )

    # Hosts válidos para el header Host (evita Host header injection)
    ALLOWED_HOSTS: str = (
        "localhost,127.0.0.1,traefik,pdf-extractor-api,*.utn.edu.ar,pdf-extractor.utn.edu.ar"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

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
        if self.MAX_FILE_SIZE_MB <= 0:
            raise RuntimeError("MAX_FILE_SIZE_MB debe ser un entero positivo.")


settings = Settings()
settings.validate()


ENVIRONMENT = settings.ENVIRONMENT
LOG_LEVEL = settings.LOG_LEVEL
MONGO_URI = settings.MONGO_URI
MONGO_DB_NAME = settings.MONGO_DB_NAME
MAX_FILE_SIZE_MB = settings.MAX_FILE_SIZE_MB
MAX_FILE_SIZE_BYTES = settings.MAX_FILE_SIZE_BYTES
ALLOWED_ORIGINS = settings.allowed_origins_list
ALLOWED_HOSTS = settings.allowed_hosts_list


def validate_config() -> None:
    settings.validate()
