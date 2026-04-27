# 📄✨ PDF Extractor API - Etapa 1

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge\&logo=fastapi)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge\&logo=mongodb\&logoColor=white)](https://www.mongodb.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge\&logo=python\&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge\&logo=docker\&logoColor=white)](https://www.docker.com/)

API REST desarrollada para la cátedra de **Desarrollo de Software (UTN FRSR)**. Se encarga de la extracción de texto de documentos PDF, validación de integridad y persistencia en base de datos NoSQL.

---

## 🛠️ Funcionalidades Implementadas (Rúbrica Etapa 1)

* [x] **Procesamiento en RAM:** Uso de `io.BytesIO` para evitar almacenamiento temporal en disco.
* [x] **Validación de Archivos:** Control estricto de extensión (.pdf) y tamaño máximo (5MB).
* [x] **Integridad de Datos:** Generación de Checksum SHA-256 para prevenir documentos duplicados.
* [x] **Base de Datos NoSQL:** Persistencia completa en MongoDB.
* [x] **CRUD Operacional:** Endpoints para Crear, Leer, Actualizar y Eliminar registros.
* [x] **Arquitectura Profesional:** Uso de variables de entorno (.env) y gestor de paquetes `uv`.

---

## 🚀 Instalación y Configuración

### 1. Requisitos Previos

* Python 3.11+
* Docker Desktop (para el motor de base de datos)
* [uv](https://docs.astral.sh/uv/) (Recomendado para gestión de entorno)

### 2. Configuración del Entorno

```bash
# Crear archivo de configuración
cp .env.example .env

# Sincronizar dependencias e instalar entorno virtual
uv sync
```

### 3. Levantar Infraestructura (Docker)

```bash
# Descargar e iniciar el contenedor de MongoDB
docker run -d --name mongo-utn -p 27017:27017 mongo:latest
```

---

## 🖥️ Ejecución de la API

Para iniciar el servidor de desarrollo:

```bash
uv run uvicorn app.main:app --reload
```

Acceso a la documentación interactiva (Swagger UI):
👉 http://127.0.0.1:8000/docs

---

## 🧪 Pruebas Automáticas (TDD)

Siguiendo la metodología de Desarrollo Orientado a Pruebas:

```bash
# Ejecutar suite de tests
uv run pytest
```

---

## 📂 Estructura del Proyecto

```text
PDF_EXTRACTOR/
├── app/              # Lógica de la aplicación
│   ├── services/     # Capa de negocio (Extracción)
│   ├── database.py   # Repositorio MongoDB
│   └── main.py       # Endpoints de FastAPI
├── tests/            # Pruebas unitarias e integración
├── .env.example      # Plantilla de configuración
├── .gitignore        # Archivos excluidos de Git
└── pyproject.toml    # Definición de dependencias
```
