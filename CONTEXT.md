# CONTEXT — PDF Extractor & Document Management API

## 1. Propósito del sistema

**PDF Extractor & Document Management API** es una API REST desarrollada para la cátedra de
Desarrollo de Software de la UTN FRSR. Permite:

- recibir un PDF por HTTP y procesarlo completamente en memoria;
- validar que el archivo sea un PDF real (magic number + parseo con `pypdf`);
- extraer su contenido y convertirlo a Markdown;
- calcular un checksum SHA-256 para detectar duplicados;
- sanitizar el nombre del archivo y el texto extraído;
- persistir el documento en MongoDB;
- listar, consultar, renombrar y eliminar documentos mediante un CRUD.

El sistema se despliega detrás de **Traefik**, que actúa como API Gateway, y expone
un health check para verificar la conectividad con MongoDB.

---

## 2. Mapa de arquitectura

La aplicación sigue una separación inspirada en **Clean Architecture**, con dependencias
dirigidas hacia el dominio y la capa de aplicación. La regla práctica es:

> La presentación no conoce MongoDB ni `pypdf`; los casos de uso reciben colaboradores
> inyectados (repositorio y extractor) que los adaptadores concretos implementan y que
> los tests sustituyen por fakes.

### 2.1 Capas

| Capa | Responsabilidad | Archivos principales |
|---|---|---|
| **Dominio** | Entidades, DTOs y errores de negocio. No conoce FastAPI ni `pymongo`. | `app/dtos.py`, `app/exceptions.py` |
| **Casos de uso / aplicación** | Orquestan validaciones, reglas de existencia, checksum, duplicados, sanitización y persistencia. | `app/use_cases/procesar_documento.py`, `app/use_cases/gestionar_documentos.py` |
| **Adaptadores de infraestructura** | Implementan la persistencia y la extracción real. | `app/database.py` (`MongoRepository`), `app/services/pdf_extractor.py` (`PyPDFExtractor`) |
| **Presentación** | Rutas HTTP, dependencias de FastAPI, middlewares y mapeo de excepciones a códigos HTTP. | `app/main.py`, `app/api/routes.py`, `app/api/dependencies.py`, `app/core/` |

### 2.2 Flujo de una subida (`POST /upload`)

```text
Cliente
  │
  ▼
FastAPI / route handler
  │  Depends(get_repositorio), Depends(get_extractor)
  ▼
ProcesarDocumentoUseCase.execute(nombre, bytes)
  │
  ├─ 1. validar tamaño (MAX_FILE_SIZE_BYTES)
  ├─ 2. sanitizar y validar nombre .pdf
  ├─ 3. is_valid_pdf (magic number + pypdf)
  ├─ 4. calculate_checksum (SHA-256)
  ├─ 5. obtener_por_checksum → rechazar duplicado
  ├─ 6. extract → Markdown
  ├─ 7. sanitize_text
  └─ 8. guardar_documento(Documento)
  │
  ▼
UploadResponse
```

### 2.3 Flujo CRUD

```text
GET    /documentos              → ListarDocumentosUseCase
GET    /documentos/{checksum}   → ObtenerDocumentoUseCase
PUT    /documentos/{checksum}   → ActualizarDocumentoUseCase
DELETE /documentos/{checksum}   → EliminarDocumentoUseCase
```

Los cuatro casos de uso validan el checksum y traducen la ausencia de un documento a
`DocumentoNoEncontradoError`. Los handlers HTTP no acceden directamente al repositorio.

### 2.4 Composición y dependencias

- `app/main.py` es el **composition root**: crea `MongoRepository` y `PyPDFExtractor`,
  los publica en `app.state` y monta la app FastAPI.
- `app/api/dependencies.py` construye los casos de uso por request con `Depends()`.
- No hay singleton global de base de datos dentro de las rutas ni mutación de casos de uso.

---

## 3. Glosario de dominio

| Término | Significado |
|---|---|
| **Documento** | Entidad persistida con `archivo`, `texto` y `hash_seguridad`. |
| **ProcesarDocumento** | Caso de uso que valida, extrae, sanitiza y persiste un PDF. |
| **RepositorioDocumentos** | Contrato de persistencia implementado por `MongoRepository` y por `FakeRepo` en tests. |
| **ExtractorPDF** | Contrato de extracción/checksum implementado por `PyPDFExtractor` y `FakeExtractor`. |
| **Checksum** | SHA-256 del contenido binario; identifica unívocamente un documento y evita duplicados. |
| **Seam** | Punto de sustitución donde se puede cambiar un adaptador sin modificar el llamador. |
| **Texto vacío** | Texto de reemplazo cuando el PDF no produce contenido extraíble. |

---

## 4. Seams acordados

Los seams son los puntos donde los tests sustituyen infraestructura por fakes:

| Seam | Interfaz / punto de entrada | Adaptador real | Adaptador de test |
|---|---|---|---|
| Caso de uso de upload | `ProcesarDocumentoUseCase.execute(filename, content_bytes, file_size=None)` | `PyPDFExtractor` + `MongoRepository` | `FakeExtractor` + `FakeRepo` |
| Persistencia | `MongoRepository` (`obtener_por_checksum`, `guardar_documento`, `listar_todos`, `actualizar_nombre`, `eliminar_documento`, `ping`) | MongoDB / `pymongo` | `FakeRepo` en memoria |
| Extracción | `PyPDFExtractor.calculate_checksum` y `extract` | `pypdf` + `hashlib` | `FakeExtractor` |
| Presentación | `build_router()` y `TestClient` | FastAPI | `TestClient` con `app.state` fake |
| Errores de dominio | `DomainException` y subclases | handler HTTP | tests unitarios de excepciones |

### Regla de test

- La lógica de aplicación se prueba **sin HTTP y sin I/O** en `tests/test_use_cases.py`.
- El contrato HTTP se prueba con `TestClient` en `tests/test_crud.py` y
  `tests/test_auxiliary_routes.py`.
- Los tests de infraestructura real (MongoDB) quedan fuera de la suite unitaria para
  mantenerla rápida y repetible.

---

## 5. Configuración centralizada

La configuración vive en **`app/core/config.py`** (el plan la menciona como
`app/config.py`; la ruta real del proyecto es `app/core/config.py`). Se carga `.env`
una sola vez y las variables ya definidas en el proceso tienen prioridad.

| Variable | Uso | Default / requisito |
|---|---|---|
| `ENVIRONMENT` | Entorno de ejecución (`development`/`production`). | `production` |
| `MONGO_URI` | URI de conexión a MongoDB. | `mongodb://localhost:27017` |
| `MONGO_DB_NAME` | Nombre de la base. | `pdf_extractor_db` |
| `MAX_FILE_SIZE_MB` | Límite de tamaño en MB. | `5` |
| `MAX_FILE_SIZE_BYTES` | Límite derivado en bytes. | `MAX_FILE_SIZE_MB * 1024 * 1024` |
| `ALLOWED_ORIGINS` | Orígenes CORS permitidos. | Lista explícita |
| `ALLOWED_HOSTS` | Hosts válidos para `TrustedHostMiddleware`. | Lista explícita |

### Validación de configuración

`app/main.py` llama a `validate_config()` al importar el composition root. La función
falla rápido con `RuntimeError` si `MAX_FILE_SIZE_MB` no es un entero positivo.

---

## 6. Guía rápida de ejecución local

### Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop (para MongoDB/Traefik)

### Instalación y tests

```bash
# 1. Sincronizar dependencias y crear el entorno virtual
uv sync

# 2. Crear configuración local
cp .env.example .env
# Editar .env: ENVIRONMENT=development

# 3. Ejecutar la suite
uv run pytest -q

# 4. Verificar estilo
uv run ruff check .
```

### Ejecución de la API

```bash
uv run uvicorn app.main:app --reload
```

La documentación interactiva queda disponible en `http://localhost:8000/docs` cuando
`ENVIRONMENT=development`.

### Ejecución completa con Docker Compose

```bash
docker compose up --build -d
```

- API a través de Traefik: `http://localhost/`
- Swagger UI: `http://localhost/docs`
- Dashboard de Traefik: `http://localhost:8080`
- MongoDB: `localhost:27017`

Para producción, definir `ENVIRONMENT=production` y el resto de variables de
configuración antes de levantar los contenedores.

---

## 7. Estado de pruebas y TDD

- Suite actual: **77 tests**, ejecutada con `uv run pytest -q`.
- Linter: `uv run ruff check .` sin observaciones.
- Los tests unitarios usan `FakeRepo`/`FakeExtractor` y no tocan MongoDB ni archivos.
- Para cada nueva funcionalidad, el proceso acordado es: **test rojo → implementación
  mínima → test verde → refactor**, dejando evidencia en el historial de Git.

---

## 8. Referencias

- `README.md` — instalación, endpoints y despliegue.
- `AUDITORIA_PROFE.md` — trazabilidad de hallazgos y estado final.
- `docs/adr/001-clean-architecture-y-seams.md` — decisión arquitectónica y consecuencias.
- `tests/fakes.py` — implementación de los adaptadores de test.
- `app/core/config.py` — fuente única de configuración.
