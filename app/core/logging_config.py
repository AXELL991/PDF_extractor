"""
Configuración de logging estructurado, rotativo y seguro para el proyecto.
Integra logging estructurado con JSON para observabilidad y auditoría.
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Any, Dict

# Constantes
LOG_DIR = os.path.join(os.getcwd(), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
SECURITY_LOG_FILE = os.path.join(LOG_DIR, "security.log")
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5


class JSONFormatter(logging.Formatter):
    """Formatter que emite logs en formato JSON estructurado."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }

        # Agregar campos extras si existen
        if hasattr(record, "client_ip"):
            log_data["client_ip"] = record.client_ip
        if hasattr(record, "user_agent"):
            log_data["user_agent"] = record.user_agent
        if hasattr(record, "request_path"):
            log_data["request_path"] = record.request_path
        if hasattr(record, "response_status"):
            log_data["response_status"] = record.response_status
        if hasattr(record, "exception"):
            log_data["exception"] = str(record.exception)

        # Agregar extra fields dinámicos
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in log_data:
                continue
            log_data[key] = value

        return json.dumps(log_data, default=str, ensure_ascii=False)


def setup_logging(
    log_level: str = "INFO",
    environment: str = "production",
) -> None:
    """Configura el sistema de logging con rotación y formato estructurado."""

    # Crear directorio de logs si no existe
    os.makedirs(LOG_DIR, exist_ok=True)

    # Nivel de logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Handler para consola con formato legible
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)

    # Handler para archivo rotativo con formato JSON
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(JSONFormatter())

    # Handler específico para eventos de seguridad
    security_handler = logging.handlers.RotatingFileHandler(
        SECURITY_LOG_FILE,
        maxBytes=MAX_BYTES // 2,
        backupCount=3,
        encoding="utf-8",
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(JSONFormatter())

    # Configurar loggers raíces
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Logger específico de seguridad
    security_logger = logging.getLogger("security")
    security_logger.setLevel(logging.DEBUG)
    security_logger.addHandler(security_handler)
    security_logger.propagate = False

    # Configurar loggers de librerías externas
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)

    # En desarrollo, mostrar más detalles
    if environment == "development":
        console_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        # En desarrollo, permitir logs de librerías
        logging.getLogger("uvicorn").setLevel(logging.INFO)
        logging.getLogger("fastapi").setLevel(logging.INFO)
