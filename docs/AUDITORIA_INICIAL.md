# Informe de Auditoría — PDF Extractor UTN

**Fecha:** 23/10/2026  
**Alcance:** `feedback_profe/analisis-arquitectura.md`, `feedback_profe/analisis-clean-code.md`, `feedback_profe/analisis-tdd.md`; `app/main.py`, `app/api/routes.py`, `app/api/dependencies.py`, `app/use_cases/`, `app/domain/`, `app/services/`, `app/core/`; `tests/`; `pyproject.toml`.  
**Método:** lectura completa de los tres informes del profesor, inspección estática con referencias `archivo:línea`, ejecución literal de `uv run pytest` y `uv run ruff check`, y verificación de imports/símbolos con `grep`.  
**Estado auditado:** árbol de trabajo local al 23/10/2026 (incluye cambios aún no commiteados).  
**Nota:** este informe reemplaza la verificación anterior de `AUDITORIA_PROFE.md`, que quedó desactualizada (hablaba de 77 tests y de símbolos ya eliminados como `is_safe_ip`, `SessionMiddleware` y `SESSION_SECRET_KEY`).

---

## 1. CHECKLIST DE OBSERVACIONES DEL PROFESOR

**Leyenda**

- **[RESUELTO]** — la corrección está implementada y es coherente con Clean Architecture, SOLID, YAGNI, KISS y DRY.
- **[PENDIENTE]** — la falla o desviación persiste total o parcialmente.

### 1.1 Informe de Arquitectura (`analisis-arquitectura.md`)

| ID | Observación del profesor | Estado | Evidencia actual |
|---|---|---|---|
| ARQ-01 | El README declara 3 capas/Clean, pero la capa de negocio está casi vacía y la orquestación vive en HTTP. | **[RESUELTO]** | La orquestación está en `app/use_cases/procesar_documento.py:49-105` y `app/use_cases/gestionar_documentos.py:31-76`; `routes.py` solo traduce HTTP. |
| ARQ-02 | La presentación llama directamente a persistencia, saltándose la capa de negocio. | **[RESUELTO]** | `app/api/routes.py` no importa ni usa `MongoRepository` para CRUD; recibe casos de uso con `Depends()` (`routes.py:13-20, 124, 150, 172, 189, 212`). |
| ARQ-03 | `validar_formato` y `validar_tamaño` estaban en HTTP y nunca se llamaban; la validación de tamaño estaba duplicada. | **[RESUELTO]** | Los helpers muertos desaparecieron. Hay una sola regla de tamaño en `validar_tamano_archivo` (`procesar_documento.py:32-46`), invocada en `:69`. |
| ARQ-04 | El health check conocía la superficie interna del adaptador (`db.client.admin.command`). | **[RESUELTO]** | `routes.py:74-95` usa `repositorio.ping()`; `MongoRepository.ping()` encapsula Mongo (`database.py:50-52`). |
| ARQ-05 | No hay puertos formales; formalizar `Protocol` con un solo adaptador sería especulativo. | **[RESUELTO]** | No se introdujeron `Protocol` decorativos. Las dependencias se aceptan por constructor (`procesar_documento.py:52-60`) y `Depends()`; se respetó la recomendación C5. |
| ARQ-06 | Los tests no cruzan un seam del dominio; parchean el singleton `app.main.db`. | **[RESUELTO]** | `tests/test_use_cases.py` prueba los casos de uso directamente con `FakeRepo`, `FakeExtractor` y `FakeChecksumCalculator` (`tests/fakes.py:9-76`); no hay `@patch`. |
| ARQ-07 | Dominio implícito: dicts crudos de Mongo, `_id` filtrado a HTTP y string mágico `"Vacio"`. | **[RESUELTO]** | Entidad pura `Documento` (`app/domain/entities.py:6-23`); mapeo Mongo→dominio (`database.py:9-15`); constante `TEXTO_VACIO` (`procesar_documento.py:21`). |
| ARQ-08 | No hay capa de aplicación ni inversión de dependencias; singletons creados en el módulo HTTP. | **[RESUELTO]** | `create_app()` como composition root (`main.py:47-94`), dependencias publicadas en `app.state` (`main.py:85-91`) y casos de uso inyectados por `Depends()`. |
| ARQ-09 | `DocumentoResponse` y `ListaDocumentosResponse` existían y no se usaban; la lista devolvía dicts crudos. | **[RESUELTO]** | DTOs usados como `response_model` y con `model_validate` (`routes.py:141-160, 162-176`). |
| ARQ-C1 | Extraer el caso de uso `ProcesarDocumento` con interfaz pequeña y dependencias inyectadas. | **[RESUELTO]** | `ProcesarDocumentoUseCase.execute(filename, content_bytes, file_size) -> ResultadoDocumento` (`procesar_documento.py:62-93`). |
| ARQ-C2 | Adelgazar `main.py` y separar configuración, rutas, middleware y handlers. | **[RESUELTO]** | `main.py` pasó de 521 a **97 líneas**; rutas en `app/api/routes.py`, config en `app/core/config.py`, middleware en `app/core/middleware.py`, handlers en `app/core/exception_handlers.py`. |
| ARQ-C3 | El repositorio debe devolver un `Documento` tipado, sin filtrar `_id`. | **[RESUELTO]** | `MongoRepository` devuelve `Documento` u `Optional[Documento]` (`database.py:26-29, 46-48`); ya no hay `pop("_id")` en HTTP. |
| ARQ-C4 | Eliminar código muerto: `validar_formato`, `validar_tamaño`, `existe_documento`, DTOs y funciones de seguridad sin uso. | **[RESUELTO]** | Los símbolos listados ya no existen. `ruff` no reporta imports muertos. Quedan vestigios de compatibilidad menores, tratados en el hallazgo residual R-01. |
| ARQ-C5 | No formalizar puertos todavía; un adaptador = seam hipotético. | **[RESUELTO]** | Decisión respetada: no hay `Protocol`; los casos de uso reciben colaboradores por parámetro y los tests usan duck typing. |
| ARQ-15 | La suite no corre por `ModuleNotFoundError: itsdangerous`. | **[RESUELTO]** | Se eliminó `SessionMiddleware` (y con él la dependencia); `uv run pytest` colecta y pasa **78 tests**. |
| ARQ-16 | Había 23 tests y el CRUD era un punto ciego que verificaba HTTP, no la orquestación. | **[RESUELTO]** | Ahora hay **78 tests**, incluidos 21 de casos de uso con orden de llamadas y efectos secundarios (`test_use_cases.py:52-286`). |
| ARQ-17 | No existía `CONTEXT.md` ni ADRs con el vocabulario/seams. | **[RESUELTO]** | `CONTEXT.md` y `docs/adr/001-clean-architecture-y-seams.md` documentan capas, seams, glosario y estrategia de tests. |

### 1.2 Informe de Clean Code (`analisis-clean-code.md`)

| ID | Observación del profesor | Estado | Evidencia actual |
|---|---|---|---|
| CC-01 | DRY: validación de tamaño copiada 3 veces. | **[RESUELTO]** | Una única regla: `validar_tamano_archivo` (`procesar_documento.py:32-46`), llamada en `:69`. |
| CC-02 | DRY: el límite estaba definido en `main.py` y `security.py`; el default aparecía en 3 lugares. | **[RESUELTO]** | Fuente única en `app/core/config.py:18-20`; `exceptions.py:3,26` consume `MAX_FILE_SIZE_MB`. |
| CC-03 | DRY: patrón “buscar documento o 404” repetido en GET, PUT y DELETE. | **[RESUELTO]** | Helper único `_obtener_documento` (`gestionar_documentos.py:18-28`), reutilizado en `:48, 58, 75`. |
| CC-04 | DRY: el `_id` de Mongo se ocultaba de dos formas distintas. | **[RESUELTO]** | El adaptador mapea a `Documento` (`database.py:9-15`); HTTP ya no conoce `_id`. |
| CC-05 | KISS: `main.py` concentraba 6 responsabilidades. | **[RESUELTO]** | `main.py` es composition root (97 líneas); responsabilidades separadas en `api/`, `core/` y `use_cases/`. |
| CC-06 | KISS/SRP: `core/security.py` era un saco de funciones sin cohesión. | **[RESUELTO]** | Paquete dividido en `sanitization.py`, `pdf_validation.py`, `checksums.py` y `tokens.py`, con fachada en `security/__init__.py`. |
| CC-07 | KISS: validación de IP por rango, condicionada a una env var apagada por defecto. | **[RESUELTO]** | La validación de IP y `is_safe_ip` fueron eliminadas por YAGNI; no quedan referencias. |
| CC-08 | KISS: `try/except` que tragaba errores de configuración de `SessionMiddleware`. | **[RESUELTO]** | `SessionMiddleware` y el `try/except` fueron eliminados; no hay silenciamiento de errores de seguridad. |
| CC-09 | KISS: `print()` en `pdf_extractor.py` en vez del logger. | **[RESUELTO]** | `logger.error(..., exc_info=True)` (`services/pdf_extractor.py:28-30`). |
| CC-10 | YAGNI: ~18 dependencias declaradas sin uso. | **[RESUELTO]** | `pyproject.toml:7-16` quedó con 8 dependencias runtime reales; dev-deps en `:24-29` (3). |
| CC-11 | YAGNI: 9 funciones/DTOs/métodos muertos. | **[RESUELTO]** | Los 9 símbolos listados (`validar_formato`, `validar_tamaño`, `hash_password`, `verify_password`, `generate_hmac`, `existe_documento`, `DocumentoResponse`, `ListaDocumentosResponse`, `PasswordHasher`) ya no existen o están en uso. |
| CC-12 | YAGNI: imports y parámetros sin uso (`contextlib`, `Any`, `Optional`, `UploadFile`). | **[RESUELTO]** | `ruff check` pasa; no hay imports huérfanos. |
| CC-S | SRP: `main.py` y `security.py` multi-responsabilidad; `PyPDFExtractor` mezclaba extracción y checksum. | **[RESUELTO]** | `main.py` y seguridad separados; `ChecksumCalculator` es un adaptador independiente (`services/checksum.py:6-11`). |
| CC-O | OCP: no había seam para nuevos formatos; `PyPDFExtractor` concreto en `main.py`. | **[RESUELTO]** | El extractor se inyecta en el caso de uso (`procesar_documento.py:52-60`); un segundo adaptador con `.extract()` es sustituible sin editar la orquestación. Se difirió el `Protocol` por YAGNI/C5. |
| CC-L | LSP: jerarquía `DomainException` coherente. | **[RESUELTO]** | Se mantiene el contrato `message`/`status_code` y los tests de excepciones (`tests/test_exceptions.py`). |
| CC-I | ISP: método muerto `existe_documento`. | **[RESUELTO]** | Eliminado; no hay interfaces formales mal segregadas. |
| CC-D | DIP: alto nivel acoplado a `MongoRepository`/`PyPDFExtractor` concretos e instanciados en `main.py`. | **[RESUELTO]** | Inyección por constructor y `Depends()`; la creación concreta vive en el composition root (`main.py:85-91`). Ver salvedad de tipado estático en el análisis técnico. |

### 1.3 Informe de TDD (`analisis-tdd.md`)

| ID | Observación del profesor | Estado | Evidencia actual |
|---|---|---|---|
| TDD-01 | La suite no arranca por `itsdangerous`. | **[RESUELTO]** | `uv run pytest` → **78 passed**. La causa (`SessionMiddleware`) fue eliminada. |
| TDD-02 | Test tautológico que recalculaba el hash con `hashlib`. | **[RESUELTO]** | `test_calculate_checksum_matches_literal` compara contra un literal SHA-256 (`test_extractor_completo.py:97-111`). |
| TDD-03 | Test de extracción solo verificaba “forma” (`isinstance(str)`). | **[RESUELTO]** | Se genera un PDF real con texto conocido y se verifica el contenido y el Markdown (`test_extractor_completo.py:12-18`; fixture en `tests/conftest.py:36-81`). |
| TDD-04 | Tests de CRUD acoplados a implementación (`@patch("app.main.db")`). | **[RESUELTO]** | `FakeRepo` se inyecta por `app.state` (`tests/fakes.py:79-88`); no hay `@patch` ni `app.main.db` en `tests/`. |
| TDD-05 | `test_upload_valid_pdf` no verificaba procesamiento real. | **[RESUELTO]** | `test_crud.py:26-39` sube un PDF real y verifica que el `Documento` persistido contiene `"Hola PDF de prueba"`. |
| TDD-06 | La rama MIME/magic no estaba cubierta. | **[RESUELTO]** | La validación pasó a `is_valid_pdf` (magic + parseo con `pypdf`, `pdf_validation.py:17-39`); cubierta por `test_security.py:73-86` y `test_crud.py:45-63`. |
| TDD-07 | No existía el seam del caso de uso. | **[RESUELTO]** | `ProcesarDocumentoUseCase.execute` (`procesar_documento.py:62-93`) es el seam de aplicación. |
| TDD-08 | El módulo de seguridad no se testeaba directamente. | **[RESUELTO]** | `tests/test_security.py` cubre `sanitize_filename`, `sanitize_text`, `validate_checksum`, `is_valid_pdf` y `generate_request_id`. |
| TDD-09 | `root`, `/health` y `/security.txt` no tenían tests. | **[RESUELTO]** | `tests/test_auxiliary_routes.py` cubre `/`, `/health` (200/503) y `/security.txt`. |
| TDD-10 | Ley 1: no hay evidencia de red-before-green; los labels “TDD” son retroactivos. | **[PENDIENTE]** | El historial reciente sigue mostrando código antes que tests (p. ej. `1b68746` refactor de casos de uso precede a `f807bc5` tests). No hay CI ni registro de un test fallando primero. Ver P-01. |
| TDD-11 | Ley 2: los tests de CRUD cargaban infraestructura de más. | **[RESUELTO]** | La lógica se prueba con fakes en `test_use_cases.py`; los tests HTTP quedaron como contrato de los endpoints. |
| TDD-12 | Ley 3: código especulativo (funciones y deps sin uso). | **[RESUELTO]** | Los símbolos y dependencias especulativas fueron eliminados; ver R-01 para vestigios menores. |
| TDD-13 | Tests como especificación: solo 14/23 verificaban comportamiento real. | **[RESUELTO]** | 78 tests con casos de éxito, error, orden de llamadas, duplicados, tamaño, PDF corrupto, sanitización y CRUD. |
| TDD-14 | No había seams pre-acordados/documentados. | **[RESUELTO]** | `CONTEXT.md` y ADR-001 documentan capas, seams y estrategia de fakes. |
| TDD-15 | Anti-patrones: tautológico, acoplado a implementación, de forma. | **[RESUELTO]** | Los tres fueron corregidos; no quedan `@patch`, `isinstance` como única aserción ni recálculo del hash en tests. |
| TDD-16 | F.I.R.S.T. / suite ejecutable. | **[RESUELTO]** | 78 tests en **4.83 s**; suite rápida y repetible. |
| TDD-17 | Brechas de cobertura: `sanitize_filename`, `sanitize_text`, `validate_checksum`, `is_valid_pdf`, `is_safe_ip`. | **[RESUELTO]** | `is_safe_ip` fue eliminada por YAGNI; el resto tiene tests directos en `test_security.py`. |
| TDD-18 | Extracción con PDF real y texto conocido nunca se verificaba. | **[RESUELTO]** | Fixture `crear_pdf_con_texto` + aserción de contenido (`conftest.py:36-81`, `test_extractor_completo.py:12-18`). |
| TDD-19 | El health check tocaba `db.client` real (canal lateral). | **[RESUELTO]** | `routes.py` usa `repositorio.ping()` y `FakeRepo.ping()` permite probar 200/503 sin Mongo. |

### 1.4 Hallazgo residual de la auditoría

| ID | Hallazgo | Estado | Evidencia |
|---|---|---|---|
| R-01 | YAGNI residual: quedan shims/alias de compatibilidad sin consumidores internos. | **[PENDIENTE]** | `app/core/security/files.py` (reexport sin imports), alias `Documento` en `app/dtos.py:47-53`, `PDF_MAGIC_NUMBERS` exportado sin uso externo (`security/__init__.py:9,14`), y reexports de `app/domain/__init__.py` y `app/services/__init__.py` no usados por el código actual. |

**Resumen del checklist:** 52 de 53 observaciones del profesor **[RESUELTO]**; 1 **[PENDIENTE]** (TDD-10, evidencia de Ley 1). Hallazgo residual adicional **[PENDIENTE]**: R-01 (limpieza YAGNI menor).

---

## 2. ANÁLISIS TÉCNICO DETALLADO

### 2.1 Arquitectura: de “2,5 capas” a capas explícitas

**ARQ-01/02/08 — La presentación ya no orquesta ni persiste.**  
`app/api/routes.py` es un adaptador fino: recibe `Request`, resuelve el caso de uso con `Depends()` y devuelve un DTO. Ejemplos: `upload_pdf` solo lee el archivo y llama `use_case.execute(...)` (`routes.py:121-139`); `listar_documentos` llama `use_case.execute()` (`:148-160`); `obtener`, `actualizar` y `borrar` delegan en sus casos de uso (`:169-221`). La orquestación de 12 pasos vive en `ProcesarDocumentoUseCase.execute` (`procesar_documento.py:62-93`): tamaño → nombre → PDF real → checksum → duplicado → extracción → sanitización → persistencia.

**ARQ-04 — El health check ya no conoce Mongo.**  
`health_check` recibe el repositorio con `Depends(get_repositorio)` y llama `repositorio.ping()` (`routes.py:74-95`). `MongoRepository.ping()` encapsula `self.client.admin.command("ping")` (`database.py:50-52`), de modo que la capa HTTP no sabe que existe un `MongoClient`.

**ARQ-07/ARQ-C3 — Dominio explícito y adaptador profundo.**  
`Documento` es un dataclass inmutable con invariantes (`app/domain/entities.py:6-23`). `MongoRepository` traduce con `_a_documento` (`database.py:9-15`) y devuelve `Documento` en `obtener_por_checksum` y `listar_todos`. El `_id` de Mongo ya no se filtra: el adaptador solo construye los campos de dominio (`archivo`, `texto`, `hash_seguridad`).

**ARQ-C1/ARQ-C2 — Casos de uso y composition root.**  
`create_app()` (`main.py:47-94`) construye la app, registra middlewares y publica dependencias en `app.state` (`:85-91`). `app/api/dependencies.py` construye un caso de uso por request (`:48-81`). Los tests usan la misma factory con fakes (`tests/fakes.py:79-88`), por lo que el seam de producción y el de test son el mismo.

**ARQ-05/ARQ-C5 — Puertos: decisión correcta de no formalizar.**  
No hay `Protocol` ni ABC decorativos. Los casos de uso aceptan colaboradores por constructor y los invocan por duck typing. Esto respeta la recomendación del profesor: un solo adaptador no justifica un puerto formal; el seam se materializará cuando exista un segundo adaptador real.

**Salvedad de tipado estático (no bloqueante).**  
`procesar_documento.py:8-17` y `gestionar_documentos.py:9` importan `MongoRepository`, `PyPDFExtractor` y `ChecksumCalculator` concretos para las anotaciones. En runtime la inversión de dependencias funciona (los fakes se inyectan sin problema), pero si la cátedra inspecciona la regla de dependencia a nivel estático, se pueden mover esos imports a `TYPE_CHECKING` con `from __future__ import annotations`. No se marca como pendiente porque el profesor recomendó explícitamente no introducir puertos todavía.

### 2.2 Clean Code: DRY, KISS, YAGNI y SOLID

**DRY (CC-01 a CC-04).**  
- Tamaño: una sola función `validar_tamano_archivo` (`procesar_documento.py:32-46`), que usa `MAX_FILE_SIZE_BYTES` de `config.py:18-20`.  
- Constantes: `MAX_FILE_SIZE_MB`/`MAX_FILE_SIZE_BYTES` solo en `config.py`; `exceptions.py` lo consume para el mensaje por defecto.  
- 404: helper `_obtener_documento` (`gestionar_documentos.py:18-28`) que valida checksum, busca y lanza `DocumentoNoEncontradoError`; lo usan GET, PUT y DELETE.  
- `_id`: el adaptador devuelve `Documento`; HTTP ya no hace `pop("_id")`.

**KISS (CC-05 a CC-09).**  
- `main.py` pasó de 521 a 97 líneas; rutas, config, middleware, rate limit y handlers están separados.  
- `app/core/security/` está dividido por responsabilidad: `sanitization.py`, `pdf_validation.py`, `checksums.py`, `tokens.py`; la fachada `__init__.py` mantiene imports estables.  
- Se eliminaron la validación de IP y `SessionMiddleware`; con ello desaparecieron el `try/except` silencioso y la dependencia `itsdangerous`.  
- `print()` fue reemplazado por `logger.error(..., exc_info=True)` en `services/pdf_extractor.py:28-30`.

**YAGNI (CC-10 a CC-12).**  
`pyproject.toml` quedó con 8 dependencias runtime (`pypdf`, `pymongo`, `python-dotenv`, `fastapi`, `uvicorn`, `python-multipart`, `slowapi`, `bleach`) y 3 dev (`httpx`, `pytest`, `ruff`). Los 9 símbolos muertos listados por el profesor ya no existen o están en uso. `ruff` no reporta imports huérfanos. El único residuo es R-01 (shims de compatibilidad), detallado en 2.4.

**SOLID.**  
- **S:** `main.py` es composition root; `routes.py` es adaptador HTTP; `use_cases/` es aplicación; `database.py`/`services/` son infraestructura. `PyPDFExtractor` ya no calcula checksums: eso vive en `ChecksumCalculator`.  
- **O:** el extractor se inyecta; un adaptador alternativo con `.extract()` puede sustituirse sin editar la orquestación. No se formalizó `Protocol` por YAGNI, tal como recomendó el profesor.  
- **L:** la jerarquía `DomainException` conserva el contrato y los tests verifican códigos 400/404/409/413/422.  
- **I:** no hay interfaces formales mal segregadas; `existe_documento` fue eliminado.  
- **D:** los casos de uso no crean sus dependencias; las reciben. La creación concreta está en `create_app()` (`main.py:85-91`) y en `dependencies.py`. Ver la salvedad de tipado estático en 2.1.

### 2.3 TDD: suite, seams y anti-patrones

**Suite y especificación (TDD-01, TDD-13, TDD-16).**  
La suite ejecuta 78 tests en 4.83 s. Los tests de casos de uso (`tests/test_use_cases.py`) verifican orden de llamadas y efectos secundarios, no solo la respuesta HTTP. Ejemplo: `test_exito_registra_orden_y_persiste` espera exactamente `calcular_checksum → obtener_por_checksum → extraer → guardar_documento` (`:82-87`). `test_duplicado_no_extrae_ni_guarda` verifica que un duplicado no llegue a extraer ni persistir (`:128-139`). `test_archivo_excedido_no_toca_dependencias` verifica que la validación de tamaño ocurra antes de tocar el repositorio/extractor (`:141-155`).

**Anti-patrones corregidos (TDD-02 a TDD-05, TDD-15).**  
- El test tautológico se reemplazó por un literal SHA-256 (`test_extractor_completo.py:97-111`).  
- El test de extracción usa un PDF real generado en memoria y verifica el texto (`test_extractor_completo.py:12-18`; `conftest.py:36-81`).  
- `test_upload_valid_pdf` verifica que el `Documento` persistido contenga el texto extraído (`test_crud.py:26-39`).  
- No quedan `@patch("app.main.db")` ni referencias a `app.main.db` en `tests/`.

**Cobertura de módulos sensibles (TDD-06, TDD-08, TDD-09, TDD-17).**  
`tests/test_security.py` prueba directamente `sanitize_filename`, `sanitize_text`, `validate_checksum`, `is_valid_pdf` y `generate_request_id`. `tests/test_auxiliary_routes.py` cubre `/`, `/health` (200/503) y `/security.txt`. La rama MIME/magic se reemplazó por una validación más fuerte: `is_valid_pdf` exige magic number y parseo real con `PdfReader` (`pdf_validation.py:17-39`), y está cubierta por tests de contenido inválido y PDF corrupto.

**Lo que no se puede resolver retroactivamente (TDD-10).**  
El historial de git no muestra un ciclo red → green: los commits de refactor de casos de uso (`1b68746`, 22/10/2026) preceden al commit de tests (`f807bc5`, 23/10/2026). Documentar el proceso en `CONTEXT.md`/ADR no constituye evidencia de que se haya practicado. Por eso TDD-10 queda **[PENDIENTE]**. Ver P-01.

### 2.4 Puntos pendientes: qué falta exactamente

#### P-01 — Evidencia de TDD (Ley 1) **[PENDIENTE]**

- **Dónde:** historial de git y ausencia de CI. `CONTEXT.md` y `docs/adr/001-clean-architecture-y-seams.md` describen la estrategia, pero no hay un registro de test rojo → verde.
- **Qué falta:** un mecanismo verificable que demuestre que cada nueva capacidad nace de un test que falla. No se puede corregir el pasado, pero sí institucionalizar el proceso.
- **Pasos exactos:**
  1. Crear `.github/workflows/ci.yml` (o equivalente) que ejecute `uv sync --dev`, `uv run pytest` y `uv run ruff check` en cada push/PR.
  2. Documentar en `CONTEXT.md` una sección “Proceso TDD” con la regla: test que falla → implementación mínima → verde → refactor.
  3. Para el próximo cambio, hacer un commit con el test fallando (o guardar la salida roja en `docs/tdd/`) y luego el commit de implementación. Eso deja evidencia para la próxima auditoría.

#### P-02 / R-01 — Limpieza YAGNI residual **[PENDIENTE]**

- **`app/core/security/files.py:1-16`:** módulo de compatibilidad que solo reexporta `PDF_MAGIC_NUMBERS`, `is_valid_pdf`, `sanitize_filename` y `sanitize_text`. No tiene ningún import en el repositorio. **Acción:** eliminarlo.
- **`app/dtos.py:47-53`:** alias `Documento = DocumentoDominio` y su entrada en `__all__`. Ningún módulo importa `Documento` desde `app.dtos`. **Acción:** eliminar el alias y la entrada de `__all__` (o documentarlo como API pública si se necesita compatibilidad externa).
- **`app/core/security/__init__.py:9,14` + `app/core/security/pdf_validation.py:11`:** `PDF_MAGIC_NUMBERS` se exporta pero solo se usa dentro de `pdf_validation.py`. **Acción:** quitar la exportación pública y el import en `security/__init__.py`; el uso interno permanece.
- **`app/domain/__init__.py:3-5` y `app/services/__init__.py:3-6`:** reexports de paquete que el código actual no consume (los imports van a los módulos concretos). **Acción:** usarlos de forma consistente o eliminarlos.
- **Verificación:** después de borrar, ejecutar `uv run pytest` y `uv run ruff check`. No hay cambio de comportamiento esperado.

#### Salvedad opcional (no pendiente): acoplamiento estático de tipos

- `app/use_cases/procesar_documento.py:8-17` y `app/use_cases/gestionar_documentos.py:9` importan adaptadores concretos para anotaciones. Si se quiere pureza estática de la regla de dependencia sin introducir `Protocol`, mover esos imports a `TYPE_CHECKING` y agregar `from __future__ import annotations`.
- `app/exceptions.py:3` importa `MAX_FILE_SIZE_MB` de `app.core.config` para el default de `TamañoExcedidoError`. El caso de uso ya pasa el límite explícito (`procesar_documento.py:46`); se podría eliminar el import y exigir el parámetro, pero no es un bloqueante.

---

## 3. VERIFICACIÓN DE SUITE DE PRUEBAS

### 3.1 Comandos ejecutados

```text
uv run pytest
```

Resultado:

```text
platform win32 -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0
rootdir: ...\PDF_extractor
configfile: pyproject.toml
testpaths: tests
collected 78 items

tests\test_app_factory.py .                                              [  1%]
tests\test_auxiliary_routes.py ....                                      [  6%]
tests\test_config.py ....                                                [ 11%]
tests\test_crud.py ...............                                       [ 30%]
tests\test_exceptions.py .......                                         [ 39%]
tests\test_extractor_completo.py ........                                [ 50%]
tests\test_security.py ..................                                [ 73%]
tests\test_use_cases.py .....................                            [100%]

============================= 78 passed in 4.83s ==============================
```

```text
uv run ruff check
```

Resultado:

```text
All checks passed!
```

Verificación adicional:

```text
uv run ruff format --check .
```

Resultado:

```text
39 files already formatted
```

### 3.2 Distribución de los 78 tests

| Archivo | Tests | Qué cubre |
|---|---:|---|
| `tests/test_app_factory.py` | 1 | Factory `create_app()` e inyección de repositorio/extractor. |
| `tests/test_auxiliary_routes.py` | 4 | `/`, `/health` (200/503) y `/security.txt`. |
| `tests/test_config.py` | 4 | Fuente única de tamaño y fail-fast de configuración. |
| `tests/test_crud.py` | 15 | Contrato HTTP del CRUD, PDF real, duplicados, 404, 400, 422. |
| `tests/test_exceptions.py` | 7 | Contrato de errores de dominio y códigos HTTP. |
| `tests/test_extractor_completo.py` | 8 | Extracción real a Markdown, errores de pypdf y checksum con literal. |
| `tests/test_security.py` | 18 | Sanitización, validación de checksum/PDF y request ID. |
| `tests/test_use_cases.py` | 21 | Orquestación del upload y CRUD con fakes, orden y efectos secundarios. |
| **Total** | **78** | |

### 3.3 Comprobaciones estructurales

- **Sin parcheo de singletons:** `grep` no encuentra `@patch`, `app.main.db`, `is_safe_ip`, `generate_csrf_token`, `SessionMiddleware`, `SESSION_SECRET_KEY` ni `ENFORCE_IP_VALIDATION` en `app/` ni en `tests/`.
- **Handlers finos:** `app/api/routes.py` tiene 223 líneas, pero cada handler solo parsea, delega y mapea DTO; no hay lógica de persistencia ni de extracción.
- **`main.py` delgado:** 97 líneas; composition root + middlewares + `include_router`.
- **Dependencias:** 8 runtime + 3 dev en `pyproject.toml`; todas tienen uso real o son requeridas por el framework (`uvicorn`, `python-multipart`).
- **Cobertura medida:** no se ejecutó `pytest-cov` porque no está en las dev-deps. La afirmación “100%” de este informe se refiere a **tests en verde**, no a un porcentaje de cobertura de líneas. Si la cátedra exige una métrica, agregar `pytest-cov` y fijar un umbral.

---

## 4. VERDICTO FINAL

### 4.1 Cumplimiento

La aplicación **cumple con los criterios técnicos de la cátedra** en los aspectos que el profesor cuestionó:

- **Clean Architecture:** dominio puro (`Documento`), capa de aplicación con cinco casos de uso, adaptadores de infraestructura y presentación fina.
- **SOLID:** SRP resuelto (main/rutas/seguridad/servicios separados); DIP resuelto por inyección de dependencias y composition root; LSP/ISP sin regresiones.
- **DRY/KISS/YAGNI:** una sola validación de tamaño, una sola fuente de configuración, un solo helper 404, sin `print`, sin `SessionMiddleware`, sin dependencias especulativas y sin los 9 símbolos muertos señalados.
- **TDD/tests:** 78 tests en verde, seams de casos de uso con fakes, PDF real, seguridad y endpoints auxiliares cubiertos; `ruff check` y `ruff format --check` limpios.

### 4.2 Lo que impide un “100% literal”

1. **TDD Ley 1 (P-01):** no hay evidencia histórica de red-before-green. Es un hecho del historial, no un defecto del código actual. Se corrige institucionalizando CI y el ciclo test-first hacia adelante; no se puede “arreglar” retroactivamente.
2. **YAGNI residual (P-02/R-01):** quedan un módulo de compatibilidad, un alias de DTO y algunos reexports sin consumidores. Son eliminables sin riesgo y no afectan el comportamiento.

Si la evaluación de la cátedra se basa en el **artefacto final** (arquitectura, código, tests y lint), el proyecto está en condiciones de **aprobación plena**. Si se evalúa la **disciplina TDD por historial**, todavía no puede demostrar el 100%: falta la evidencia de P-01.

### 4.3 Pasos exactos para cerrar el 100%

1. **Eliminar R-01:** borrar `app/core/security/files.py`; quitar el alias `Documento` de `app/dtos.py`; dejar de exportar `PDF_MAGIC_NUMBERS` desde `app/core/security/__init__.py`; limpiar los reexports no usados de `app/domain/__init__.py` y `app/services/__init__.py`.
2. **Verificar:** `uv run pytest` (78 verdes) y `uv run ruff check` (sin observaciones).
3. **Agregar CI:** `.github/workflows/ci.yml` con `uv sync --dev`, `uv run pytest` y `uv run ruff check`.
4. **Documentar y practicar TDD:** sección “Proceso TDD” en `CONTEXT.md`; para el próximo cambio, commit del test rojo antes de la implementación.
5. **Commitear el estado actual:** el árbol tiene archivos modificados y nuevos sin commit (`app/domain/`, `app/core/security/pdf_validation.py`, `app/core/security/sanitization.py`, `app/services/checksum.py`, `tests/test_app_factory.py`, entre otros). Para que la auditoría sea reproducible, conviene commitear todo el refactor y luego repetir `pytest`/`ruff`.
6. **Opcional, si la rúbrica exige cobertura numérica:** agregar `pytest-cov` y ejecutar `uv run pytest --cov=app --cov-report=term-missing`, fijando un umbral en `pyproject.toml`.

**Conclusión:** el proyecto ya no tiene los bloqueantes que motivaron los tres informes del profesor. Queda **un pendiente de proceso** (evidencia TDD) y **una limpieza menor de YAGNI**; ambos son acotados y no afectan el funcionamiento ni la arquitectura lograda.
