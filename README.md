# 📄✨ PDF Extractor API - Etapa 1

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Traefik](https://img.shields.io/badge/Traefik-24A1C1?style=for-the-badge&logo=traefik&logoColor=white)](https://traefik.io/)

API REST desarrollada para la cátedra de **Desarrollo de Software (UTN FRSR)**. Se encarga de la extracción de contenido estructurado en **Markdown** a partir de documentos PDF, validación de integridad (SHA-256) y persistencia en base de datos NoSQL (MongoDB), todo expuesto a través de **Traefik API Gateway**.

---

## Integrantes - Legajo

* Puita Axel 10903
* Cerda Santiago 10802
* Serpa Juan Cruz 10938

---

## 🛠️ Funcionalidades Implementadas (Rúbrica Etapa 1)

* [x] **Procesamiento en RAM:** Uso de `io.BytesIO` para evitar almacenamiento temporal en disco.
* [x] **Extracción a Markdown:** Conversión y preservación de estructura de páginas, encabezados y listas en Markdown limpio.
* [x] **Validación de Archivos:** Control estricto de extensión (.pdf), magic numbers binarios y tamaño máximo (5MB).
* [x] **Integridad de Datos:** Generación de Checksum SHA-256 para prevenir documentos duplicados.
* [x] **Base de Datos NoSQL:** Persistencia completa en MongoDB.
* [x] **CRUD Operacional:** Endpoints para Crear, Leer, Actualizar y Eliminar registros.
* [x] **API Gateway (Traefik):** Entrada unificada en puerto 80 con proxy inverso y dashboard.
* [x] **Arquitectura Limpia & Casos de Uso:** Separación clara entre capas, endpoints, casos de uso y repositorios.
* [x] **Manejo de Excepciones:** Excepciones personalizadas del dominio con códigos HTTP apropiados.
* [x] **Dominio Puro y DTOs Tipados:** Entidad `Documento` como dataclass inmutable y esquemas Pydantic solo en la capa API.

---

## 🏗️ Arquitectura del Proyecto

```
                         [ Cliente / Frontend ]
                                    │
                                    │ HTTP :80
                                    ▼
                      ┌───────────────────────────┐
                      │    Traefik API Gateway    │
                      │   Dashboard en :8080      │
                      └─────────────┬─────────────┘
                                    │
                      ┌─────────────▼─────────────┐
                      │   FastAPI Application     │
                      │  - create_app() factory   │
                      │  - Rutas y Middlewares    │
                      │  - ProcesarDocumentoUseCase│
                      └───┬─────────┬─────────┬───┘
                          │         │         │
        ┌─────────────────▼──┐  ┌───▼───────┐ │
        │  PyPDFExtractor    │  │ Checksum  │ │
        │  (Extracción       │  │ Calculator│ │
        │   Markdown)        │  │ (SHA-256) │ │
        └────────────────────┘  └───────────┘ │
                                  ┌───────────▼──────────┐
                                  │  MongoRepository     │
                                  │  (Persistencia en    │
                                  │   MongoDB)           │
                                  └──────────────────────┘
```

### 📚 Documentación de arquitectura

- [`CONTEXT.md`](CONTEXT.md) — propósito, mapa de capas, glosario, seams y guía de ejecución.
- [`docs/adr/001-clean-architecture-y-seams.md`](docs/adr/001-clean-architecture-y-seams.md) — decisión de Clean Architecture, inyección de dependencias y fakes.

---

## 🚀 Instalación y Configuración

### 1. Requisitos Previos

* Python 3.11+
* Docker Desktop
* [uv](https://docs.astral.sh/uv/) (Recomendado para gestión de dependencias)

### 2. Configuración del Entorno

```bash
# Crear archivo de configuración
cp .env.example .env

# Sincronizar dependencias e instalar entorno virtual
uv sync
```

> Toda la configuración de entorno se centraliza en `app/core/config.py` y se valida
> al iniciar. El límite de tamaño se controla con `MAX_FILE_SIZE_MB`.

### 3. Levantar Todo con Docker Compose (Traefik + Mongo + API)

```bash
docker compose up --build -d
```

- **API a través del Gateway:** `http://localhost/` o `http://localhost/docs` (Puerto 80)
- **Dashboard de Traefik:** `http://localhost:8080`
- **MongoDB:** `localhost:27017`

---

## 🧪 Pruebas Unitarias y de Integración

Para correr la suite de tests automatizada:

```bash
uv run pytest
```
