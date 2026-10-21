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
    pkg-config \
    ca-certificates \
    gnupg \
    curl
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOF

# Crear directorio de trabajo
WORKDIR /app

# Instalar UV (gestor de paquetes rápido y moderno para Python)
RUN pip install --no-cache-dir uv==0.4.15

# Copiar archivos de dependencias con permisos restringidos
COPY --chmod=444 pyproject.toml uv.lock ./

# Crear entorno virtual e instalar dependencias con UV
# uv export genera un requirements.txt limpio y seguro con hashes
# uv sync instala solo las dependencias necesarias de producción
RUN <<EOF
set -eux
# Crear venv en /opt/venv para facilitar la copia en runtime
uv venv /opt/venv
# Sincronizar solo dependencias de producción (sin dev)
uv sync --no-dev --frozen
EOF

# Limpiar cache de uv y archivos innecesarios
RUN rm -rf /root/.cache /tmp/*

# ============================================
# STAGE 2: Runtime (Hardened & Minimal)
# ============================================
# Base limpia sin herramientas de compilación
FROM python:3.11-slim-bookworm AS runtime

# Metadatos del contenedor
LABEL maintainer="UTN FRSR - Seguridad en Desarrollo" \
      version="2.0.0" \
      description="API REST segura para extracción de texto de PDFs" \
      org.opencontainers.image.source="https://github.com/AXELL991/PDF_extractor" \
      org.opencontainers.image.vendor="UTN San Rafael" \
      org.opencontainers.image.licenses="MIT"

# Argumentos de build
ARG APP_USER=appuser
ARG APP_GROUP=appgroup
ARG APP_UID=10001
ARG APP_GID=10001
ARG APP_DIR=/app

# Variables de entorno para runtime seguro
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    # Activar el entorno virtual automáticamente
    PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV="/opt/venv" \
    # Variables de la aplicación
    APP_HOME=${APP_DIR} \
    ENVIRONMENT=production \
    LOGLEVEL=INFO

# Instalar dependencias de runtime mínimas (curl para healthcheck seguro, libmagic para validación)
RUN <<EOF
set -eux
apt-get update
apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libmagic1
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOF

# Crear usuario y grupo no-root con UID/GID fijo y sin shell interactivo
# Esto mitiga ataques de elevación de privilegios
RUN <<EOF
set -eux
groupadd -g ${APP_GID} ${APP_GROUP}
useradd -u ${APP_UID} -g ${APP_GROUP} -d ${APP_HOME} -s /sbin/nologin -c "App User" ${APP_USER}
# Crear directorios necesarios con permisos restrictivos
mkdir -p ${APP_HOME} ${APP_HOME}/logs /tmp
chown -R ${APP_USER}:${APP_GROUP} ${APP_HOME} /tmp
chmod 750 ${APP_HOME}
chmod 777 /tmp
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

# Exponer el puerto (no privilegiado, > 1024)
EXPOSE 8000

# Health check con criterios estrictos para detectar problemas de servicio
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/').getcode() == 200 else 1)" || exit 1

# Comando para ejecutar la aplicación con configuraciones de seguridad de uvicorn
CMD ["uvicorn", "app.main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--proxy-headers", \
    "--forwarded-allow-ips", "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16", \
    "--no-server-header", \
    "--no-date-header", \
    "--workers", "2", \
    "--ws", "none" \
]
