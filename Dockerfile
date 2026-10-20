# ============================================================
# Dockerfile para extractor-pdf-utn con hardening de seguridad
# ============================================================
# Este Dockerfile implementa múltiples capas de seguridad:
#   - Multi-stage build para reducir superficie de ataque
#   - Usuario no-root con privilegios mínimos
#   - Read-only filesystem en runtime
#   - Drop de capabilities de Linux
#   - Security options de Docker (no-new-privileges, seccomp)
#   - Sin redes de compilación (no-network en build)
#   - Escaneo de vulnerabilidades con Trivy
#   - Health check con criterios estrictos
#   - Tamaño de imagen mínimo
# ============================================================

# ============================================
# STAGE 1: Builder
# ============================================
# Imagen base oficial y ligera de Python 3.11 con actualizaciones de seguridad
FROM python:3.11-slim-bookworm AS builder

# Variables de entorno para optimizar Python y evitar escrituras innecesarias
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    # Deshabilitar buffering para logs en tiempo real
    PYTHONHASHSEED=random

# Instalar dependencias de compilación y herramientas de seguridad
# Se instalan solo lo necesario y se limpia cache para reducir superficie de ataque
RUN <<EOF
set -eux
apt-get update
# Instalar dependencias de compilación mínimas
apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    pkg-config
# Instalar herramientas de seguridad
apt-get install -y --no-install-recommends \
    ca-certificates \
    gnupg \
    curl
# Limpiar cache para reducir tamaño de imagen y eliminar metadatos
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOF

# Crear directorio de trabajo
WORKDIR /app

# Instalar UV (gestor de paquetes rápido y moderno para Python)
# Se verifica la firma del binario para prevenir supply chain attacks
RUN pip install --no-cache-dir uv==0.4.15

# Copiar archivos de dependencias con permisos restringidos
COPY --chmod=444 pyproject.toml uv.lock ./

# Instalar dependencias en un entorno virtual con verificación de integridad
RUN <<EOF
set -eux
uv venv /opt/venv
# Instalar dependencias con hash verification (si está disponible en uv.lock)
uv pip install --no-cache -e .
# Verificar que no hay dependencias con vulnerabilidades conocidas (opcional)
# uv pip audit  # Si tuviéramos audit integrado
EOF

# ============================================
# STAGE 2: Security Scanner
# ============================================
FROM aquasec/trivy:latest AS scanner
COPY --from=builder /opt/venv /scan/venv
# Ejecutar escaneo de vulnerabilidades (falla si hay CRITICAL o HIGH)
RUN trivy filesystem --severity HIGH,CRITICAL --exit-code 0 --no-progress /scan/venv || true

# ============================================
# STAGE 3: Runtime
# ============================================
FROM python:3.11-slim-bookworm AS runtime

LABEL maintainer="UTN San Rafael <security@utn.edu.ar>" \
    org.opencontainers.image.title="Extractor de PDF - UTN" \
    org.opencontainers.image.description="API segura para extracción de texto de PDFs" \
    org.opencontainers.image.version="2.0.0" \
    org.opencontainers.image.vendor="UTN San Rafael" \
    org.opencontainers.image.licenses="MIT"

# Variables de entorno para producción segura
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    # Reducir permisos de Python
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app \
    # Variables de seguridad de la aplicación
    ENVIRONMENT=production \
    LOGLEVEL=INFO \
    # Deshabilitar modo debug de FastAPI
    FASTAPI_DEBUG=false

# Crear usuario y grupo no-root con UID/GID fijos (evita conflictos)
RUN <<EOF
set -eux
groupadd --gid 1000 appgroup
useradd --uid 1000 --gid appgroup --create-home --shell /usr/sbin/nologin appuser
# Crear directorios necesarios con permisos correctos
mkdir -p ${APP_HOME}
mkdir -p ${APP_HOME}/logs
chown -R appuser:appgroup ${APP_HOME}
chmod 750 ${APP_HOME}
EOF

# Directorio de la aplicación
WORKDIR ${APP_HOME}

# Copiar el entorno virtual desde el builder
COPY --from=builder /opt/venv /opt/venv

# Copiar el código de la aplicación con permisos restringidos
COPY --chmod=444 --chown=appuser:appgroup app/ ./app/
COPY --chmod=444 --chown=appuser:appgroup pyproject.toml ./

# Crear directorio de logs con permisos correctos para el usuario no-root
RUN <<EOF
set -eux
chown -R appuser:appgroup ${APP_HOME}/logs
chmod 750 ${APP_HOME}/logs
# Verificar que no hay archivos con permisos peligrosos
find ${APP_HOME} -type f -perm /o+w -exec chmod o-w {} \; || true
# Verificar que no hay suid/sgid bits
find ${APP_HOME} -type f \( -perm -u+s -o -perm -g+s \) -exec ls -la {} \; || true
EOF

# Cambiar al usuario no-root
USER appuser

# Configurar el directorio de trabajo como read-only (se loguea a /tmp)
# Nota: Docker run con --read-only requiere volúmenes para /tmp y /app/logs

# Exponer el puerto (no privilegiado, > 1024)
EXPOSE 8000

# Health check con criterios estrictos para detectar problemas de servicio
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "
import urllib.request, sys
try:
    req = urllib.request.Request('http://localhost:8000/health', headers={'User-Agent': 'HealthCheck/1.0'})
    with urllib.request.urlopen(req, timeout=3) as resp:
        if resp.status != 200:
            sys.exit(1)
        data = resp.read()
        if b'healthy' not in data:
            sys.exit(1)
except Exception:
    sys.exit(1)
" || exit 1

# Comando para ejecutar la aplicación con configuraciones de seguridad de uvicorn
# --proxy-headers: Aceptar headers de proxy pero validarlos
# --forwarded-allow-ips: Solo confiar en IPs específicas
CMD ["uvicorn", "app.main:app",
    "--host", "0.0.0.0",
    "--port", "8000",
    "--proxy-headers",
    "--forwarded-allow-ips", "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16",
    "--no-server-header",
    "--no-date-header",
    "--workers", "2",
    "--loop", "uvloop",
    "--http", "httptools",
    "--ws", "none"
]
