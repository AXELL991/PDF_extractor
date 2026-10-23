# ============================================================
# Dockerfile para extractor-pdf-utn con hardening de seguridad
# ============================================================

# ============================================
# STAGE 1: Builder
# ============================================
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    pkg-config \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar UV
RUN pip install --no-cache-dir uv==0.4.15

# Copiar archivos de dependencias
COPY pyproject.toml uv.lock ./

# Crear entorno virtual e instalar dependencias directamente en /opt/venv
RUN uv sync --no-dev --frozen

# ============================================
# STAGE 2: Runtime (Hardened & Minimal)
# ============================================
FROM python:3.11-slim-bookworm AS runtime

LABEL maintainer="UTN FRSR - Seguridad en Desarrollo" \
      version="2.0.0" \
      description="API REST segura para extracción de texto de PDFs"

ARG APP_USER=appuser
ARG APP_GROUP=appgroup
ARG APP_UID=10001
ARG APP_GID=10001
ARG APP_DIR=/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV="/opt/venv" \
    APP_HOME=${APP_DIR} \
    ENVIRONMENT=production \
    LOGLEVEL=INFO

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario y grupo no-root
RUN groupadd -g ${APP_GID} ${APP_GROUP} && \
    useradd -u ${APP_UID} -g ${APP_GROUP} -d ${APP_HOME} -s /sbin/nologin -c "App User" ${APP_USER} && \
    mkdir -p ${APP_HOME} ${APP_HOME}/logs /tmp && \
    chown -R ${APP_USER}:${APP_GROUP} ${APP_HOME} /tmp && \
    chmod 750 ${APP_HOME} && \
    chmod 777 /tmp

WORKDIR ${APP_HOME}

# Copiar el entorno virtual con uvicorn y dependencias instaladas
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# Copiar código fuente
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup pyproject.toml ./

RUN chown -R appuser:appgroup ${APP_HOME}/logs && \
    chmod 750 ${APP_HOME}/logs

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/').getcode() == 200 else 1)" || exit 1

CMD ["uvicorn", "app.main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--proxy-headers", \
    "--forwarded-allow-ips", "*", \
    "--no-server-header", \
    "--no-date-header", \
    "--workers", "2" \
]
