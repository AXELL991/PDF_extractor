# 📄✨ PDF Extractor API - Etapa 1

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

API REST desarrollada para la cátedra de **Desarrollo de Software (UTN FRSR)**. Se encarga de la extracción de texto de documentos PDF, validación de integridad y persistencia en base de datos NoSQL.

---

## Integrantes - Legajo

* Puita axel 10903
* Cerda Santiago 10802
* Serpa Juan Cruz 10938

---

## 🛠️ Funcionalidades Implementadas (Rúbrica Etapa 1)

* [x] **Procesamiento en RAM:** Uso de `io.BytesIO` para evitar almacenamiento temporal en disco.
* [x] **Validación de Archivos:** Control estricto de extensión (.pdf) y tamaño máximo (5MB).
* [x] **Integridad de Datos:** Generación de Checksum SHA-256 para prevenir documentos duplicados.
* [x] **Base de Datos NoSQL:** Persistencia completa en MongoDB.
* [x] **CRUD Operacional:** Endpoints para Crear, Leer, Actualizar y Eliminar registros.
* [x] **Arquitectura en Capas:** Separación clara entre presentación, negocio y datos.
* [x] **Manejo de Excepciones:** Excepciones personalizadas del dominio con códigos HTTP apropiados.
* [x] **DTOs Tipados:** Respuestas de API con Pydantic para validación automática.

---

## 🏗️ Arquitectura del Proyecto

El proyecto sigue una **arquitectura en capas** simple pero efectiva:

```
┌─────────────────────────────────────────┐
│           CAPA DE PRESENTACIÓN          │
│              (main.py)                  │
│     - Endpoints FastAPI                 │
│     - Validaciones de entrada           │
│     - Manejo de excepciones             │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│           CAPA DE NEGOCIO               │
│      (services/pdf_extractor.py)        │
│     - Extracción de texto PDF           │
│     - Generación de checksum SHA-256    │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│           CAPA DE DATOS                 │
│         (database.py)                   │
│     - Conexión MongoDB                  │
│     - Operaciones CRUD                  │
└─────────────────────────────────────────┘
```

### Componentes Adicionales

- **DTOs** (`dtos.py`): Objetos de transferencia de datos con Pydantic
- **Excepciones** (`exceptions.py`): Errores del dominio (FormatoInvalido, DocumentoDuplicado, etc.)

---

## 🚀 Instalación y Configuración

### 1. Requisitos Previos

* Python 3.11+
* Docker Desktop (para el motor de base de datos)
* [uv](https://docs.astral.sh/uv/) (Recomendado para gestión de entorno)

### 2. Configuración del Entorno (en terminal de visual studio)

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

El proyecto cuenta con **23 tests** organizados por funcionalidad:

| Suite | Tests | Descripción |
|-------|-------|-------------|
| `test_extractor_completo.py` | 5 | Tests de la capa de negocio (extracción y checksum) |
| `test_crud.py` | 12 | Tests de integración para todas las operaciones CRUD |
| `test_exceptions.py` | 6 | Tests de excepciones personalizadas |

### Ejecutar Tests

```bash
# Ejecutar todos los tests
uv run pytest

# Ejecutar con verbose
uv run pytest -v

# Ejecutar solo tests de CRUD
uv run pytest tests/test_crud.py -v

# Ejecutar con cobertura
uv run pytest --cov=app
```

### Tests Implementados

- ✅ Extracción de texto de PDFs
- ✅ Generación consistente de checksums SHA-256
- ✅ Validación de formatos (solo PDF)
- ✅ Prevención de documentos duplicados
- ✅ Listado de documentos (vacío y con datos)
- ✅ Búsqueda por checksum (éxito y error 404)
- ✅ Actualización de nombres (éxito y error 404)
- ✅ Eliminación de documentos (éxito y error 404)

---

## 📂 Estructura del Proyecto

```text
PDF_EXTRACTOR/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Endpoints FastAPI + manejo de excepciones
│   ├── database.py             # Repositorio MongoDB (CRUD completo)
│   ├── dtos.py                 # DTOs Pydantic para respuestas API
│   ├── exceptions.py           # Excepciones personalizadas del dominio
│   └── services/
│       ├── __init__.py
│       └── pdf_extractor.py    # Lógica de extracción de PDF
├── tests/
│   ├── __init__.py
│   ├── test_extractor_completo.py   # Tests unitarios del extractor
│   ├── test_crud.py                 # Tests de integración CRUD
│   └── test_exceptions.py           # Tests de excepciones
├── .env.example                # Plantilla de configuración
├── .gitignore
├── pyproject.toml              # Dependencias y metadatos del proyecto
└── README.md
```

---

## 🔌 Endpoints de la API

### Estado
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Verifica que la API esté online |

### Documentos (CRUD)
| Método | Endpoint | Descripción | Códigos de Respuesta |
|--------|----------|-------------|---------------------|
| POST | `/upload` | Subir y procesar PDF | 200, 400, 409, 413 |
| GET | `/documentos` | Listar todos los PDFs | 200 |
| GET | `/documentos/{checksum}` | Buscar por hash SHA-256 | 200, 404 |
| PUT | `/documentos/{checksum}` | Actualizar nombre | 200, 404 |
| DELETE | `/documentos/{checksum}` | Eliminar documento | 200, 404 |

---

## 🧹 Principios de Clean Code Aplicados

- **Nombres Intencionales**: `validar_formato()`, `verificar_duplicado()`
- **Funciones Pequeñas**: Cada función hace una sola cosa
- **Sin Comentarios Innecesarios**: El código es su propia documentación
- **Manejo de Errores**: Excepciones en lugar de códigos de retorno
- **Separación de Responsabilidades**: Cada capa tiene su función clara
