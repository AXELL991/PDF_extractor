"""Configuración centralizada de la aplicación, leída del entorno."""

import os

from dotenv import load_dotenv

# Carga .env una sola vez para toda la aplicación. Las variables ya definidas
# en el proceso tienen prioridad sobre el archivo.
load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "production").strip().lower()
LOG_LEVEL = os.getenv("LOGLEVEL", "INFO")

# Configuración de base de datos
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pdf_extractor_db")

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


def validate_config() -> None:
    """Valida la configuración que debe fallar rápido al arrancar."""
    if MAX_FILE_SIZE_MB <= 0:
        raise RuntimeError("MAX_FILE_SIZE_MB debe ser un entero positivo.")
