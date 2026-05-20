# ============================================
# STAGE 1: Builder
# ============================================
# Imagen base oficial y ligera de Python 3.11
FROM python:3.11-slim AS builder

# Variables de entorno para optimizar Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias de compilacion (necesarias para algunas libs de Python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Instalar UV (gestor de paquetes rapido y moderno para Python)
RUN pip install uv

# Copiar archivos de dependencias
COPY pyproject.toml uv.lock ./

# Instalar dependencias en un entorno virtual
RUN uv venv /opt/venv && \
    uv pip install --no-cache -e .

# ============================================
# STAGE 2: Runtime
# ============================================
FROM python:3.11-slim AS runtime

# Variables de entorno para produccion
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app

# Crear usuario no-root para seguridad
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --create-home appuser

# Directorio de la aplicacion
WORKDIR ${APP_HOME}

# Copiar el entorno virtual desde el builder
COPY --from=builder /opt/venv /opt/venv

# Copiar el codigo de la aplicacion
COPY app/ ./app/

# Cambiar permisos al usuario no-root
RUN chown -R appuser:appgroup ${APP_HOME}

# Cambiar al usuario no-root
USER appuser

# Exponer el puerto (no privilegiado, > 1024)
EXPOSE 8000

# Healthcheck para verificar que la API esta funcionando
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Comando para ejecutar la aplicacion
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
