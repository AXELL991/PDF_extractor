"""Configuración centralizada de la aplicación, leída del entorno."""

import os
import secrets

from dotenv import load_dotenv

# Carga .env una sola vez para toda la aplicación. Las variables ya definidas
# en el proceso tienen prioridad sobre el archivo.
load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "production").strip().lower()
LOG_LEVEL = os.getenv("LOGLEVEL", "INFO")

# Configuración de base de datos
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pdf_extractor_db")

# Configuración de seguridad
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
ENFORCE_IP_VALIDATION = os.getenv("ENFORCE_IP_VALIDATION", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Configuración de tamaño de archivo (única fuente de verdad)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Orígenes CORS permitidos (solo los configurados explícitamente)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8080,https://pdf-extractor.utn.edu.ar",
    ).split(",")
    if origin.strip()
]

# Hosts válidos para el header Host (evita Host header injection)
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1,traefik,pdf-extractor-api,*.utn.edu.ar,pdf-extractor.utn.edu.ar",
    ).split(",")
    if host.strip()
]


def validate_config(
    environment: str | None = None,
    session_secret_key: str | None = None,
) -> None:
    """Valida la configuración que debe fallar rápido al arrancar.

    En producción el secreto de sesión es obligatorio. En desarrollo se permite
    un fallback aleatorio explícito a través de ``get_session_secret_key``.
    """
    env = ENVIRONMENT if environment is None else environment.strip().lower()
    secret = SESSION_SECRET_KEY if session_secret_key is None else session_secret_key

    if env == "production" and not secret:
        raise RuntimeError(
            "SESSION_SECRET_KEY es obligatoria en producción. "
            "Defínila en el entorno antes de iniciar la aplicación."
        )

    if MAX_FILE_SIZE_MB <= 0:
        raise RuntimeError("MAX_FILE_SIZE_MB debe ser un entero positivo.")


def get_session_secret_key() -> str:
    """Devuelve el secreto de sesión validado o un fallback solo para desarrollo."""
    validate_config()
    if SESSION_SECRET_KEY:
        return SESSION_SECRET_KEY
    return secrets.token_urlsafe(32)
