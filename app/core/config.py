"""Configuración centralizada de la aplicación, leída del entorno."""

import os

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
LOG_LEVEL = os.getenv("LOGLEVEL", "INFO")

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
        "localhost,127.0.0.1,*.utn.edu.ar,pdf-extractor.utn.edu.ar",
    ).split(",")
    if host.strip()
]
