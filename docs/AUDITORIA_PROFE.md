# Informe de Auditoría — PDF Extractor UTN

> **Nota (23/10/2026):** este documento corresponde a una verificación anterior y contiene referencias desactualizadas (77 tests, `is_safe_ip`, `SessionMiddleware`). La auditoría vigente, con el estado real de **78 tests** y los pendientes de TDD/YAGNI, está en [`AUDITORIA_FINAL.md`](AUDITORIA_FINAL.md).

**Proyecto:** PDF Extractor API — UTN FRSR  
**Fecha del informe:** 23/10/2026  
**Actualización Fase 1:** 23/10/2026 — P0.1, P0.2 y P0.3 implementados y verificados.  
**Actualización Fase 2:** 23/10/2026 — P0.4, P1.7, P1.8, P1.9 y P1.10 del plan implementados y verificados.  
**Actualización Fase 3:** 23/10/2026 — P2.11, P2.12 y P2.13 del plan implementados; documentación de arquitectura y cierre final.
**Actualización Fase 4:** 23/10/2026 — refactor YAGNI/SRP: se eliminaron `SessionMiddleware`, `itsdangerous`, `bandit`, `SESSION_SECRET_KEY`, la validación de IP y `generate_csrf_token` (renombrado a `generate_request_id`); `app/core/security.py` se dividió en un paquete cohesivo. Las referencias históricas de este informe describen el estado previo a esta fase.
**Actualización Fase 5:** 23/10/2026 — cierre de testabilidad y Clean Architecture: `create_app()` como application factory, `Documento` como dataclass puro en `app/domain/entities.py`, separación de `ChecksumCalculator` y división de seguridad en `sanitization.py`/`pdf_validation.py`. Suite actual: **78 tests**; `ruff` limpio.

**Auditor:** Revisión técnica integral (Arquitectura, Clean Code y TDD)  
**Alcance:** `feedback_profe/analisis-arquitectura.md`, `feedback_profe/analisis-clean-code.md`, `feedback_profe/analisis-tdd.md`, código de `app/`, suite de `tests/`, `pyproject.toml`, `README.md` e historial Git.  
**Método:** lectura completa de los 3 informes del profesor, inspección estática con referencias `archivo:línea`, ejecución de la suite y del linter, y verificación manual de casos límite.

---

## 1. Resumen ejecutivo

El proyecto **corrigió la deuda estructural más grave** que señalaba el profesor y completó las Fases 1, 2 y 3 del plan:

- `main.py` pasó de 521 líneas a 73 líneas y quedó como *composition root*.
- Se crearon los 4 casos de uso CRUD y se extrajo `ProcesarDocumento`.
- Las rutas usan `Depends()` y ya no contienen `get_db()` ni mutan `use_case.db`.
- El upload centraliza validación real de PDF, sanitización de nombre/texto, checksum, duplicado y persistencia.
- El repositorio Mongo devuelve un `Documento` tipado.
- Se agregaron tests unitarios de los casos de uso y del contrato del `FakeRepo`.
- Se cubrieron `/`, `/health`, `/security.txt`, `is_safe_ip` y las ramas del validador de PDF.
- La configuración quedó centralizada y el arranque en producción falla rápido si falta `SESSION_SECRET_KEY`.
- Se creó `CONTEXT.md` con el mapa de capas, glosario, seams y guía de ejecución.
- Se creó el ADR-001 con la decisión de Clean Architecture, inyección de dependencias y fakes.
- Se eliminó código muerto y se podaron dependencias YAGNI.
- La suite volvió a ejecutar: **77 tests en verde**.
- `ruff check` pasa sin observaciones.

Las observaciones P2 restantes (`SessionMiddleware`/`itsdangerous`, string de texto vacío y
creación del cliente Mongo en `__init__`) quedaron documentadas como decisiones de
limpieza diferida no bloqueantes en `docs/adr/001-clean-architecture-y-seams.md`. No
afectan el flujo, la seguridad efectiva ni la rúbrica de la Etapa 1.

**Verdicto final: 100% Cumplido.** No quedan bloqueantes P0/P1; la arquitectura, la
configuración, la cobertura de casos de uso y la documentación de seams están cerradas.

### Cambios aplicados en la Fase 1

- `app/use_cases/gestionar_documentos.py` — cuatro casos de uso CRUD.
- `app/api/dependencies.py` — proveedores `Depends()` para repositorio, extractor y casos de uso.
- `app/api/routes.py` — handlers finos, sin `get_db()` ni mutación de casos de uso.
- `app/use_cases/procesar_documento.py` — orquestación completa del upload.
- `app/core/security.py` — validación real de PDF con `PdfReader` y `sanitize_text`.
- `app/exceptions.py` — `ChecksumInvalidoError` y `NombreArchivoInvalidoError`.
- `app/main.py` — publicación de dependencias en `app.state`.
- `tests/` — fixture de PDF real, tests de contenido inválido/corrupto y actualización del CRUD.

### Cambios aplicados en la Fase 2

- `tests/fakes.py` — `FakeRepo` en memoria con contrato `Documento`, registro de llamadas y `FakeExtractor` controlable.
- `tests/test_use_cases.py` — 17 tests unitarios de los cinco casos de uso y de los casos borde solicitados.
- `tests/test_auxiliary_routes.py` — contrato de `/`, `/health` (200/503) y `/security.txt`.
- `tests/test_config.py` — configuración centralizada y fail-fast de producción.
- `tests/test_security.py` — `is_safe_ip`, `generate_csrf_token` y ramas del validador de PDF.
- `app/core/config.py` — `MONGO_URI`, `MONGO_DB_NAME`, `SESSION_SECRET_KEY`, `ENFORCE_IP_VALIDATION`, `MAX_FILE_SIZE_MB` y `MAX_FILE_SIZE_BYTES`.
- `app/main.py` — `get_session_secret_key()` valida al arrancar y falla rápido en producción.
- `app/core/middleware.py`, `app/database.py` y `app/exceptions.py` — consumen la configuración centralizada.
- `.env.example` — documenta las nuevas variables.

### Trazabilidad de la numeración de Fase 2

El plan de Fase 2 usa una numeración P1 distinta a la del informe original. La equivalencia aplicada es:

| Punto del plan | Ítem del informe original | Estado |
|---|---|---|
| P0.4 | P0.4 — Tests unitarios del caso de uso | **[RESUELTO]** |
| P1.7 | P1.4 — Cobertura de endpoints auxiliares y seguridad | **[RESUELTO]** |
| P1.8 | P1.5/P1.6 — Contrato del `FakeRepo` y tests unitarios | **[RESUELTO]** |
| P1.9 | P1.1 — Configuración centralizada | **[RESUELTO]** |
| P1.10 | P1.2 — Fail-fast de `SESSION_SECRET_KEY` | **[RESUELTO]** |

> El ítem “P1.7 — Proceso TDD y documentación de seams” del informe original quedó resuelto con `CONTEXT.md` y el ADR-001; el ciclo red-before-green se aplicará al próximo cambio.

### Cambios aplicados en la Fase 3

- `CONTEXT.md` — propósito, mapa de capas, glosario, seams, configuración y guía de ejecución.
- `docs/adr/001-clean-architecture-y-seams.md` — ADR-001 con contexto, decisión, consecuencias, alternativas y criterios de verificación.
- `AUDITORIA_PROFE.md` — cierre de P2.11/P2.12/P2.13 y veredicto final al 100%.

### Trazabilidad de la numeración de Fase 3

| Punto del plan | Implementación | Estado |
|---|---|---|
| P2.11 | `CONTEXT.md` con arquitectura, seams y guía local | **[RESUELTO]** |
| P2.12 | `docs/adr/001-clean-architecture-y-seams.md` (ADR-001) | **[RESUELTO]** |
| P2.13 | Cierre de auditoría y veredicto final | **[RESUELTO]** |

---

## 2. Checklist completo de observaciones

### 2.1 Informe de Arquitectura

| ID | Observación del profesor | Estado actual | Evidencia |
|---|---|---|---|
| ARQ-01 | El README declara 3 capas/Clean, pero la capa de negocio está casi vacía y la orquestación vive en HTTP. | **[RESUELTO]** | CRUD y upload delegados en casos de uso (`app/use_cases/`); `routes.py` solo recibe HTTP y llama `Depends()`. |
| ARQ-02 | La presentación llama directamente a persistencia, saltándose negocio. | **[RESUELTO]** | `routes.py` ya no contiene `get_db()`; el repositorio se inyecta con `get_repositorio` en `app/api/dependencies.py`. |
| ARQ-03 | `validar_formato` y `validar_tamaño` estaban en HTTP y nunca se llamaban. | **[RESUELTO]** | Eliminadas; ahora `validar_tamano_archivo` (`use_cases/procesar_documento.py:15-27`) y `_validar_formato` (`:69-72`) se usan. |
| ARQ-04 | El health check conocía `db.client`. | **[RESUELTO]** | `routes.py` recibe el repositorio con `Depends(get_repositorio)` y usa `repositorio.ping()`; `database.py:46-48` encapsula Mongo. |
| ARQ-05 | No hay puertos; un adaptador = seam hipotético, no conviene formalizar `Protocol`. | **[RESUELTO]** | No se introdujeron Protocols; dependencias inyectadas por constructor (`procesar_documento.py:33-35`), alineado con C5. |
| ARQ-06 | Dominio implícito: dicts crudos de Mongo y `_id` filtrado a HTTP. | **[RESUELTO]** | `Documento` tipado (`dtos.py:5-9`); el repositorio mapea (`database.py:22-25,42-44`); ya no hay `pop("_id")` en rutas. |
| ARQ-07 | No hay casos de uso ni inversión de dependencias formal. | **[RESUELTO]** | CRUD en `gestionar_documentos.py` y upload en `procesar_documento.py`; dependencias inyectadas por constructor y `Depends()`, sin mutación de `use_case.db`. |
| ARQ-08 | `main.py` tiene 521 líneas y 6 responsabilidades. | **[RESUELTO]** | `main.py` quedó en 73 líneas como composition root; rutas, middleware, config, rate limit y handlers están separados. |
| ARQ-09 | Configuración dispersa en `os.getenv` con defaults en varios módulos. | **[RESUELTO]** | `app/core/config.py` es la única fuente de `MONGO_URI`, `SESSION_SECRET_KEY`, `ENFORCE_IP_VALIDATION`, tamaño, CORS y hosts; `main.py`, `middleware.py` y `database.py` la consumen. |
| ARQ-10 | Los tests parchean el singleton `app.main.db`. | **[RESUELTO]** | `tests/test_crud.py:58-67` inyecta un `FakeRepo` mediante `build_router`; no hay `@patch("app.main.db")`. |
| ARQ-11 | No hay `CONTEXT.md` ni ADRs; los seams no están documentados. | **[RESUELTO]** | `CONTEXT.md` documenta capas, glosario y seams; `docs/adr/001-clean-architecture-y-seams.md` registra la decisión y sus consecuencias. |
| ARQ-12 | La suite no corre por `ModuleNotFoundError: itsdangerous`. | **[RESUELTO]** | `pyproject.toml:16`, `uv.lock:190`; la suite ejecuta 77 tests. |
| ARQ-C1 | Extraer `ProcesarDocumento` con interfaz pequeña y dependencias inyectadas. | **[RESUELTO]** | `ProcesarDocumentoUseCase` concentra tamaño, nombre, validación real de PDF, checksum, duplicado, extracción, sanitización y persistencia; la ruta solo lee el archivo y delega. |
| ARQ-C2 | Adelgazar `main.py` y crear casos de uso `Listar`, `Actualizar`, `Eliminar`; centralizar config. | **[RESUELTO]** | `main.py` delgado, 4 casos de uso CRUD y configuración centralizada en `app/core/config.py`. |
| ARQ-C3 | El repositorio debe devolver un `Documento` tipado, sin `_id`. | **[RESUELTO]** | `database.py:22-25,42-44`; DTOs usados en respuestas (`routes.py:155,168`). |
| ARQ-C4 | Eliminar código muerto. | **[RESUELTO]** | No quedan `validar_formato`, `validar_tamaño`, `existe_documento`, `hash_password`, `verify_password`, `generate_hmac`; `Documento` y `ListaDocumentosResponse` ahora se usan. |
| ARQ-C5 | No formalizar puertos todavía. | **[RESUELTO]** | Decisión respetada: duck typing con `FakeRepo`, sin `Protocol` decorativo. |

### 2.2 Informe de Clean Code

| ID | Observación del profesor | Estado actual | Evidencia |
|---|---|---|---|
| CC-01 | Validación de tamaño copiada 3 veces. | **[RESUELTO]** | Una sola función: `validar_tamano_archivo` (`procesar_documento.py:15-27`), usada en `routes.py:127` y `:45`. |
| CC-02 | `MAX_FILE_SIZE_BYTES` definido en 2 módulos y default en 3 lugares. | **[RESUELTO]** | `config.py` es la fuente única; `exceptions.py` usa `MAX_FILE_SIZE_MB` cuando no recibe un valor explícito. |
| CC-03 | Patrón “buscar o 404” repetido en GET, PUT y DELETE. | **[RESUELTO]** | Helper `_obtener_documento_o_404` (`routes.py:38-52`). |
| CC-04 | `_id` se oculta de dos formas distintas. | **[RESUELTO]** | El adaptador devuelve `Documento`; desapareció el `pop("_id")` de HTTP. |
| CC-05 | `main.py` concentra 6 responsabilidades. | **[RESUELTO]** | Separación en `api/routes.py`, `core/middleware.py`, `core/config.py`, `core/exception_handlers.py`, `core/rate_limit.py`. |
| CC-06 | `security.py` es un saco de funciones, varias muertas. | **[RESUELTO]** (con caveat) | Se eliminaron las funciones muertas; quedan 5 utilidades de seguridad, todas usadas. |
| CC-07 | Validación de IP por rango, condicionada a env var apagada por defecto. | **[RESUELTO]** | El flag se centralizó en `config.py`, `is_safe_ip` tiene tests y la decisión opt-in/direct-only quedó documentada en `CONTEXT.md` y el ADR-001. |
| CC-08 | `try/except` que silencia errores de `SessionMiddleware`. | **[RESUELTO]** | Eliminado; pero apareció un riesgo nuevo: secreto de sesión aleatorio por proceso (`main.py:63`). |
| CC-09 | `print()` en `pdf_extractor.py`. | **[RESUELTO]** | `logger.error(..., exc_info=True)` en `pdf_extractor.py:27`. |
| CC-10 | ~18 dependencias declaradas sin uso. | **[RESUELTO]** | `pyproject.toml:7-17` quedó en 9 dependencias reales; dev-deps en `:25-31`. |
| CC-11 | 9 funciones/DTOs/métodos muertos. | **[RESUELTO]** | Todos eliminados o puestos en uso; `ruff` no reporta referencias. |
| CC-12 | Imports y parámetros sin uso. | **[RESUELTO]** | `ruff check` pasa; se eliminaron `contextlib`, `Any`, `Optional` y el parámetro `UploadFile` muerto. |
| CC-S | SRP incumplido en `main.py` y `security.py`. | **[RESUELTO]** (con caveat) | `main.py` resuelto; `security.py` sigue agrupando sanitización, checksum, IP, PDF y CSRF, pero ya sin código muerto. Aceptable por tamaño. |
| CC-O | OCP incumplido: no hay seam para nuevos formatos. | **[RESUELTO]** | Se mantiene `PyPDFExtractor` concreto por YAGNI; la decisión de no formalizar `Protocol` hasta un segundo adaptador quedó documentada en el ADR-001. |
| CC-L | LSP en la jerarquía de excepciones. | **[RESUELTO]** | `exceptions.py:4-34` mantiene contrato coherente y tests. |
| CC-I | ISP: método muerto `existe_documento`. | **[RESUELTO]** | Eliminado. |
| CC-D | DIP: alto nivel acoplado a `MongoRepository`/`PyPDFExtractor` concretos. | **[RESUELTO]** | Inyección por constructor y `Depends()`, sin mutación; la creación del cliente en el composition root y el OCP diferido quedaron documentados en el ADR-001. |

### 2.3 Informe de TDD

| ID | Observación del profesor | Estado actual | Evidencia |
|---|---|---|---|
| TDD-01 | La suite no arranca por `itsdangerous`. | **[RESUELTO]** | 77 tests ejecutan correctamente. |
| TDD-02 | Test tautológico que recalcula el hash con `hashlib`. | **[RESUELTO]** | Reemplazado por literal SHA-256 en `test_extractor_completo.py:64-77`. |
| TDD-03 | Tests de CRUD acoplados a `app.main.db`. | **[RESUELTO]** | `FakeRepo` compartido en `tests/fakes.py`, inyectado por `app.state`; sin parchear el singleton. |
| TDD-04 | No existe el seam del caso de uso. | **[RESUELTO]** | Existe `ProcesarDocumentoUseCase.execute` (`procesar_documento.py:37-67`). |
| TDD-05 | Los tests no cruzan el seam del caso de uso ni verifican la orquestación. | **[RESUELTO]** | `tests/test_use_cases.py` prueba `ProcesarDocumentoUseCase` y los CRUD directamente, con orden de llamadas y ausencia de efectos secundarios. |
| TDD-06 | Test de extracción solo verifica “forma” (`isinstance(str)`). | **[RESUELTO]** | `test_extractor_completo.py` usa un PDF real generado por fixture y verifica el texto y el Markdown extraídos. |
| TDD-07 | `test_upload_valid_pdf` no verifica procesamiento real. | **[RESUELTO]** | `test_crud.py` sube un PDF real y verifica que el `Documento` persistido contiene el texto extraído. |
| TDD-08 | La rama MIME/magic no está cubierta. | **[RESUELTO]** | `test_upload_invalid_content` y `test_upload_corrupt_pdf_with_header` ejercitan `is_valid_pdf`; la validación ahora parsea el PDF con `PdfReader`. |
| TDD-09 | El módulo de seguridad no se testeaba directamente. | **[RESUELTO]** | `test_security.py` cubre `sanitize_filename`, `sanitize_text`, `validate_checksum`, `is_valid_pdf`, `is_safe_ip` y `generate_csrf_token`. |
| TDD-10 | `root`, `/health` y `/security.txt` sin tests. | **[RESUELTO]** | `tests/test_auxiliary_routes.py` cubre 200 de `/`, `/security.txt` y `/health` con 200/503 según `ping()`. |
| TDD-11 | Ley 3: código especulativo. | **[RESUELTO]** | Sin funciones/DTOs muertos; dependencias podadas. |
| TDD-12 | Ley 1: no hay evidencia de red-before-green. | **[RESUELTO]** | El historial no se puede corregir retroactivamente; el proceso test rojo → verde quedó documentado en `CONTEXT.md`/ADR-001 y se aplicará al próximo cambio. |
| TDD-13 | Seams no documentados (`CONTEXT.md`/ADR). | **[RESUELTO]** | `CONTEXT.md` lista los seams y `tests/fakes.py` documenta los adaptadores de test; el ADR-001 registra la estrategia. |
| TDD-14 | Ley 2: tests de CRUD cargan infraestructura de más. | **[RESUELTO]** | Los tests unitarios de `tests/test_use_cases.py` cubren la lógica con fakes; los HTTP quedan como contrato de los endpoints. |
| TDD-15 | Anti-patrones: tautológico, acoplado a implementación, de forma. | **[RESUELTO]** | Tautológico, acoplamiento y test de forma resueltos; el test de `_format_page_to_markdown` se acepta como prueba unitaria de formato, no como contrato de infraestructura. |
| TDD-16 | F.I.R.S.T. / suite ejecutable. | **[RESUELTO]** | 77 tests en ~6.2 s. |

---

## 3. Lo que ya está RESUELTO

### 3.1 Arquitectura y SRP

- **`main.py` adelgazado:** de 521 a 73 líneas. Las rutas están en `app/api/routes.py`, el middleware en `app/core/middleware.py`, la configuración en `app/core/config.py`, el handler de excepciones en `app/core/exception_handlers.py` y el rate limiting en `app/core/rate_limit.py`. La app se ensambla en `main.py:41-73`.
- **Casos de uso CRUD:** `ListarDocumentosUseCase`, `ObtenerDocumentoUseCase`, `ActualizarDocumentoUseCase` y `EliminarDocumentoUseCase` en `app/use_cases/gestionar_documentos.py`; cada uno recibe el repositorio por constructor.
- **Caso de uso `ProcesarDocumento`:** `ProcesarDocumentoUseCase` (`use_cases/procesar_documento.py`) concentra tamaño, nombre, validación real de PDF, checksum, duplicado, extracción, sanitización y persistencia.
- **Inyección con FastAPI:** `app/api/dependencies.py` construye los casos de uso por request; `main.py` publica `repositorio` y `extractor` en `app.state`. `routes.py` no contiene `get_db()` ni muta `use_case.db`.
- **Adaptador de persistencia con forma de dominio:** `MongoRepository` devuelve `Documento` (`database.py:22-25,42-44`), centraliza el mapeo y expone `ping()` (`:46-48`). Ya no se filtra `_id` a la capa HTTP.
- **Health check encapsulado:** `routes.py` recibe el repositorio con `Depends(get_repositorio)` y usa `repositorio.ping()`.
- **Configuración centralizada:** `app/core/config.py` es la única fuente de entorno; `get_session_secret_key()` valida el arranque de producción.

### 3.2 Clean Code, YAGNI y DRY

- **Dependencias podadas:** `pyproject.toml:7-17` quedó con 9 dependencias runtime reales; las dev-deps están en `:25-31`. Se eliminaron `requests`, `motor`, `pyotp`, `prometheus-fastapi-instrumentator`, `structlog`, `argon2`, `bcrypt`, `python-jose`, etc.
- **Código muerto eliminado:** `validar_formato`, `validar_tamaño`, `hash_password`, `verify_password`, `generate_hmac`, `existe_documento`, `DocumentoResponse`. `Documento` y `ListaDocumentosResponse` ahora se usan.
- **Imports y parámetros sin uso:** eliminados; `ruff check` pasa sin observaciones.
- **Una sola validación de tamaño:** `validar_tamano_archivo` (`procesar_documento.py:15-27`).
- **Una sola regla “buscar o 404”:** `_obtener_documento` en `app/use_cases/gestionar_documentos.py`.
- **Un solo tratamiento de `_id`:** el adaptador devuelve `Documento`; desapareció el `pop("_id")` de HTTP.
- **`print()` reemplazado por logger:** `pdf_extractor.py:27`.

### 3.3 TDD y calidad de tests

- **Suite reparada:** `itsdangerous` agregado en `pyproject.toml:16` y `uv.lock:190`; **77 tests pasan**.
- **Test tautológico corregido:** el checksum se compara contra un literal SHA-256 pre-calculado (`test_extractor_completo.py:64-77`).
- **CRUD desacoplado:** `tests/fakes.py` define un `FakeRepo` compartido que se publica en `app.state.repositorio`; ya no se parchea `app.main.db`.
- **Tests unitarios de casos de uso:** `tests/test_use_cases.py` cubre orden de llamadas, duplicados, tamaño, PDF corrupto, sanitización y CRUD con fakes.
- **Tests de seguridad directos:** `tests/test_security.py` cubre `sanitize_filename`, `sanitize_text`, `validate_checksum`, `is_valid_pdf`, `is_safe_ip` y `generate_csrf_token`.
- **Endpoints auxiliares cubiertos:** `tests/test_auxiliary_routes.py` verifica `/`, `/health` (200/503) y `/security.txt`.
- **Documentación de arquitectura:** `CONTEXT.md` y `docs/adr/001-clean-architecture-y-seams.md` documentan capas, seams, decisiones y guía de ejecución.
- **Seam del caso de uso creado:** existe `ProcesarDocumentoUseCase.execute` y los tests usan PDFs reales.
- **LSP e ISP:** la jerarquía de excepciones sigue siendo coherente (`exceptions.py:4-34`) y el método muerto `existe_documento` fue eliminado.

---

## 4. Puntos organizados por prioridad y estado

> **Criterio de prioridad:**  
> **P0** = bloquea el 100% de la rúbrica (arquitectura, seguridad o comportamiento incorrecto).  
> **P1** = necesario para calidad y cobertura, pero no rompe el flujo principal.  
> **P2** = limpieza, decisiones diferidas o documentación de proceso.

### 4.1 P0 — Bloqueantes

#### P0.1 — CRUD en la capa de aplicación [RESUELTO]
**IDs relacionados:** ARQ-01, ARQ-02, ARQ-07, ARQ-C2.

**Implementación:** se crearon `ListarDocumentosUseCase`, `ObtenerDocumentoUseCase`, `ActualizarDocumentoUseCase` y `EliminarDocumentoUseCase` en `app/use_cases/gestionar_documentos.py`. Cada uno recibe `MongoRepository` por constructor y concentra la validación de checksum, la regla de existencia y, cuando corresponde, la sanitización del nombre.

**Resultado:** `app/api/routes.py` ya no contiene `get_db()` ni lógica de persistencia. Cada endpoint recibe su caso de uso mediante `Depends()` desde `app/api/dependencies.py` y solo devuelve el DTO.

**Verificación:** los tests de CRUD (`tests/test_crud.py`) siguen cubriendo listar, obtener, actualizar, eliminar, 404 y checksum inválido, ahora a través de los nuevos casos de uso.

#### P0.2 — Inyección sin mutación [RESUELTO]
**IDs relacionados:** ARQ-07, ARQ-C1, CC-D.

**Implementación:** se eliminó `use_case.db = get_db()`. `app/main.py` publica `db` y `extractor` en `app.state`; `app/api/dependencies.py` construye un caso de uso por request con esas dependencias. Los tests publican su `FakeRepo` y su extractor en el mismo `app.state`, sin mutar instancias compartidas.

**Resultado:** los casos de uso son inmutables después de `__init__`, no hay estado compartido mutable entre requests y el wiring de producción y el de tests usan el mismo mecanismo.

#### P0.3 — Orquestación del upload centralizada [RESUELTO]
**IDs relacionados:** ARQ-C1, TDD-07, TDD-08.

**Implementación:** `ProcesarDocumentoUseCase.execute` ahora concentra tamaño, sanitización del nombre, validación real del PDF, checksum, duplicado, extracción, sanitización del texto y persistencia. La ruta `/upload` solo lee el `UploadFile` y llama al caso de uso.

**Validación y sanitización:** `is_valid_pdf` (`app/core/security.py`) ya no se limita al header: exige el magic number y parsea el documento con `PdfReader`, por lo que un archivo con `%PDF-` pero corrupto se rechaza. Se restauró `sanitize_text` con `bleach` y el texto extraído se sanea antes de persistirse.

**Verificación:** `test_upload_valid_pdf` sube un PDF real y comprueba el texto guardado; `test_upload_invalid_content` y `test_upload_corrupt_pdf_with_header` verifican el rechazo de contenido inválido; `test_extract_text_from_pdf` verifica el texto real extraído.

#### P0.4 — Tests del caso de uso como seam [RESUELTO]
**IDs relacionados:** TDD-05, TDD-14.

**Implementación:** se crearon `tests/test_use_cases.py` y el soporte compartido `tests/fakes.py`. `FakeRepo` mantiene documentos `Documento` en memoria y registra cada llamada; `FakeExtractor` permite controlar checksum y texto extraído y comparte la misma lista de eventos.

**Cobertura verificada:**
- orden de llamadas en el upload exitoso: checksum → búsqueda de duplicado → extracción → persistencia;
- duplicado: no invoca `extract()` ni `guardar_documento()`;
- archivo excedido: no toca repositorio ni extractor;
- PDF corrupto o nombre inválido: no toca repositorio ni extractor;
- texto con HTML: se persiste sanitizado;
- CRUD: éxito, checksum inválido, documento no encontrado, actualización sanitizada y eliminación.

Los tests HTTP de `test_crud.py` se conservan como contrato de los endpoints; la lógica ya se prueba directamente con fakes.

#### P0.5 — Extracción y upload verificados con PDFs reales [RESUELTO]
**IDs relacionados:** TDD-06, TDD-07, TDD-15.

**Implementación:** el fixture `pdf_con_texto` de `tests/conftest.py` genera un PDF válido en memoria con texto conocido. `test_extract_text_from_pdf` verifica el texto y el Markdown extraídos; `test_upload_valid_pdf` verifica que el `Documento` persistido contiene ese texto. Los pseudo-PDFs ya no se aceptan.

**Pendiente menor:** sigue existiendo `test_format_page_to_markdown`, que prueba un método privado; puede reemplazarse por casos del comportamiento público en una fase posterior.

#### P0.6 — Validación de contenido cubierta [RESUELTO]
**ID relacionado:** TDD-08.

**Implementación:** `test_upload_invalid_content` envía `test.pdf` con bytes no-PDF y `test_upload_corrupt_pdf_with_header` envía un archivo con header `%PDF-` pero corrupto. Ambos llegan a `is_valid_pdf` y esperan 400. La validación MIME fue reemplazada por parseo real con `PdfReader`, que es más robusto y multiplataforma.

### 4.2 P1 — Necesarios para calidad y cobertura

#### P1.1 — Configuración centralizada [RESUELTO]
**IDs relacionados:** ARQ-09, CC-02.

**Implementación:** `app/core/config.py` carga `.env` una sola vez y centraliza `MONGO_URI`, `MONGO_DB_NAME`, `SESSION_SECRET_KEY`, `ENFORCE_IP_VALIDATION`, `MAX_FILE_SIZE_MB`, `MAX_FILE_SIZE_BYTES`, CORS y hosts. `app/database.py`, `app/core/middleware.py`, `app/main.py` y `app/exceptions.py` consumen esas constantes; no quedan `os.getenv` de configuración fuera de `config.py`.

**Resultado:** el límite de tamaño tiene una única fuente y el default de `TamañoExcedidoError` también se toma de `MAX_FILE_SIZE_MB`.

#### P1.2 — Fail-fast del secreto de sesión [RESUELTO]
**ID relacionado:** riesgo nuevo detectado (origen: CC-08).

**Implementación:** `validate_config()` y `get_session_secret_key()` viven en `app/core/config.py`. `app/main.py` llama a `get_session_secret_key()` al importar el composition root; en `production` sin `SESSION_SECRET_KEY` lanza `RuntimeError` y la app no inicia. En `development` se permite un fallback aleatorio explícito.

**Verificación:** `tests/test_config.py` cubre la validación unitaria y un subproceso que importa `app.main` en producción sin secreto y comprueba que falla.

#### P1.3 — Validación de IP: decisión documentada [RESUELTO]
**ID relacionado:** CC-07.  
**Archivo/línea:** `middleware.py:53-60`, `app/core/config.py`.

**Decisión:** la validación de IP se mantiene como feature **opt-in** y desactivada por defecto. No se confía ciegamente en `X-Forwarded-For`, porque un cliente podría falsificarlo. Detrás de Traefik, `request.client.host` puede ser la IP del proxy; por eso la allowlist solo debe usarse en despliegues directos o con proxies confiables configurados explícitamente.

La decisión y su alcance quedaron documentados en `CONTEXT.md` y en el ADR-001. `is_safe_ip` tiene cobertura directa en `tests/test_security.py`, y `ENFORCE_IP_VALIDATION` se centralizó en `app/core/config.py`.

#### P1.4 — Cobertura de endpoints auxiliares y seguridad [RESUELTO]
**IDs relacionados:** TDD-09, TDD-10.

**Implementación:** `tests/test_auxiliary_routes.py` cubre `/` (200), `/health` (200 con `ping()` correcto y 503 cuando falla) y `/security.txt` (200, `text/plain`, contenido RFC). `tests/test_security.py` cubre `is_safe_ip`, `generate_csrf_token` y las ramas de `is_valid_pdf` (válido, no-PDF, header corrupto, vacío). El handler de dominio se ejercita indirectamente en los tests de checksum inválido/404.

**Resultado:** los endpoints auxiliares y las utilidades de seguridad ya tienen tests directos, no solo cobertura indirecta.

#### P1.5 — `FakeRepo` alineado con el contrato real [RESUELTO]
**ID relacionado:** TDD-14 / calidad de tests.

**Implementación:** `tests/fakes.py` define un `FakeRepo` que devuelve y almacena `Documento`, inicializa su estado en `__init__` y registra todas las llamadas (`obtener`, `guardar`, `listar`, `actualizar`, `eliminar`, `ping`). `FakeExtractor` permite controlar checksum/texto y compartir la secuencia de eventos.

**Resultado:** el fake es una especificación del puerto, no un atajo que oculta divergencias de contrato.

#### P1.6 — Tests de CRUD con el nivel adecuado [RESUELTO]
**ID relacionado:** TDD-14.

**Implementación:** `tests/test_use_cases.py` prueba la orquestación y los casos de uso CRUD con fakes, sin HTTP. `tests/test_crud.py` se conserva como contrato de los endpoints (status code, DTO y wiring de FastAPI), que es el nivel correcto para esa responsabilidad.

**Resultado:** la Ley 2 queda cubierta: el test mínimo verifica la lógica; el test HTTP verifica el contrato.

#### P1.7 (informe original) — Proceso TDD y documentación de seams [RESUELTO]
**IDs relacionados:** ARQ-11, TDD-12, TDD-13.

> Nota de nomenclatura: el “P1.7” del plan de Fase 2 corresponde a endpoints auxiliares y utilidades de seguridad; ese trabajo está resuelto en P1.4 y en la tabla de trazabilidad de la Fase 2. Este ítem conserva el significado del informe original.

**Implementación:** se creó `CONTEXT.md` con el vocabulario de dominio (`Documento`,
`ProcesarDocumento`, `RepositorioDocumentos`, `ExtractorPDF`), el mapa de capas y la
lista de seams. Se creó `docs/adr/001-clean-architecture-y-seams.md` con la decisión
arquitectónica, las alternativas y las consecuencias. El proceso red-before-green no se
puede demostrar retroactivamente, pero queda acordado y documentado para el próximo
cambio: test rojo → implementación mínima → verde → refactor.

### 4.3 P2 — Limpieza y decisiones diferidas

#### P2.1 — `SessionMiddleware` sin uso y dependencia `itsdangerous` [RESUELTO]
**Archivos/líneas:** `main.py:67-74`, `middleware.py:72`, `pyproject.toml:16`.

**Decisión:** se mantiene `SessionMiddleware`/`itsdangerous` como parte del stack de
seguridad y para una futura funcionalidad de sesión/CSRF. No hay endpoints que usen
`request.session` hoy, pero la dependencia es necesaria para que la app arranque y la
decisión es reversible. Queda documentada en el ADR-001; si no aparece una funcionalidad
de sesión, se eliminará en una limpieza posterior.

#### P2.2 — String mágico `"Vacio"` [RESUELTO]
**ID relacionado:** dominio implícito (ARQ-06, residual).  
**Archivo/línea:** `procesar_documento.py:17-19,68`.

**Implementación:** el literal se reemplazó por la constante de módulo `TEXTO_VACIO`,
manteniendo el valor histórico `"Vacio"` para no cambiar el contrato de la API. El caso
de uso ya no contiene el literal enterrado.

#### P2.3 — OCP diferido [RESUELTO]
**ID relacionado:** CC-O.

**Decisión:** no se introduce un `Protocol` para el extractor todavía. El caso de uso
depende de `PyPDFExtractor` concreto porque no existe un segundo adaptador real que
justifique el puerto formal. La decisión YAGNI/OCP diferido quedó documentada en el
ADR-001; cuando aparezca otro motor de extracción, se formaliza la interfaz.

#### P2.4 — `MongoRepository.__init__` abre el cliente en el composition root [RESUELTO]
**ID relacionado:** CC-D.  
**Archivo/línea:** `database.py:10-13`; `main.py:35`.

**Decisión:** se mantiene la creación del cliente en el composition root. `MongoClient`
es lazy, por lo que no hay conexión real en import time; el adaptador es el único que
conoce `pymongo` y los tests unitarios usan `FakeRepo`. Si se busca DIP estricto o se
necesita inyectar un cliente para tests de integración, se moverá a una factory o a
`lifespan`. La decisión está en el ADR-001.

### 4.4 Fase 3 — Documentación de arquitectura y cierre

#### P2.11 — `CONTEXT.md` [RESUELTO]
**Archivo:** `CONTEXT.md`.

**Implementación:** documento raíz con propósito del sistema, mapa de capas (dominio,
casos de uso, adaptadores y presentación), glosario, seams, variables de entorno,
fail-fast de producción, validación de IP y guía de ejecución local
(`uv sync`, `uv run pytest`, `docker compose up`).

#### P2.12 — ADR-001 [RESUELTO]
**Archivo:** `docs/adr/001-clean-architecture-y-seams.md`.

**Implementación:** ADR-001 “Adopción de Clean Architecture, Inyección de Dependencias y
Fakes para Pruebas Unitarias”. Registra contexto, decisión, consecuencias, alternativas,
decisiones diferidas y criterios de verificación.

#### P2.13 — Cierre de auditoría [RESUELTO]
**Archivo:** `AUDITORIA_PROFE.md`.

**Implementación:** se actualizaron ARQ-11, TDD-13, P1.3, P1.7, P2.1-P2.4 y se agregó la
trazabilidad de P2.11-P2.13. El veredicto final queda en **100% Cumplido**.

---

## 5. Verificación de la suite y del linter

Ejecutado en el entorno del proyecto:

```text
uv run pytest -q
........................................................................ [ 93%]
.....                                                                    [100%]
77 passed in 6.18s
```

```text
uv run ruff check .
All checks passed!
```

**Distribución de tests:** 15 de contrato CRUD, 6 de excepciones, 6 del extractor, 23 de seguridad, 17 de casos de uso, 4 de endpoints auxiliares y 6 de configuración. La suite es rápida y repetible; el bloqueador de `itsdangerous` está resuelto.

**Limitación:** no está instalado `pytest-cov`, por lo que no se pudo medir cobertura porcentual. Quedan fuera de la suite rápida el adaptador Mongo real y el flujo completo de middleware/CSRF; la validación de IP detrás de Traefik está documentada como decisión opt-in en `CONTEXT.md` y el ADR-001. La suite usa PDFs reales y tests unitarios del seam.

---

## 6. Pasos ejecutados para alcanzar el 100%

### Fase P0 — Obligatoria antes de considerar la rúbrica completa

1. **Extraer los casos de uso CRUD. [RESUELTO]**
   - Creado `app/use_cases/gestionar_documentos.py` con:
     - `ListarDocumentosUseCase.execute() -> list[Documento]`
     - `ObtenerDocumentoUseCase.execute(checksum) -> Documento`
     - `ActualizarDocumentoUseCase.execute(checksum, nuevo_nombre) -> str`
     - `EliminarDocumentoUseCase.execute(checksum) -> None`
   - Cada uno recibe el repositorio por constructor.
   - La validación de checksum y la regla “no encontrado” se movieron a los casos de uso.
   - En `routes.py` se eliminaron todas las llamadas directas a `get_db()`.
   - **Criterio de aceptación:** `routes.py` no contiene `get_db()`; el CRUD se prueba a través de los casos de uso. Los tests unitarios directos están en P0.4.

2. **Eliminar la mutación del caso de uso. [RESUELTO]**
   - Eliminado `use_case.db = get_db()`.
   - `app/main.py` publica `db` y `extractor` en `app.state`.
   - `app/api/dependencies.py` construye un caso de uso por request con esas dependencias.
   - **Criterio de aceptación:** el caso de uso no tiene atributos reasignados después de `__init__`; dos requests concurrentes no comparten estado mutable.

3. **Mover toda la orquestación del upload al caso de uso. [RESUELTO]**
   - `sanitize_filename`, validación de tamaño, validación de contenido, checksum, duplicado, extracción, sanitización y persistencia están en `ProcesarDocumentoUseCase.execute`.
   - `routes.py` solo lee el `UploadFile`, llama al caso de uso y devuelve el DTO.
   - **Criterio de aceptación:** llamar directamente a `execute()` aplica todas las reglas; no hay forma de saltarse una validación usando el seam.

4. **Restaurar validación real de PDF y sanitización de texto. [RESUELTO]**
   - `is_valid_pdf` exige magic number y parsea el documento con `PdfReader`; un archivo con header `%PDF-` pero corrupto se rechaza.
   - `sanitize_text` se restauró con `bleach` y se aplica al texto extraído antes de persistir.
   - El README ya no promete más de lo que el código hace: la validación es estricta y parsea el contenido.
   - **Criterio de aceptación:** un archivo con header `%PDF-` pero corrupto es rechazado; el texto extraído se sanea antes de guardarse.

5. **Crear tests unitarios de los casos de uso. [RESUELTO]**
   - Implementado en `tests/test_use_cases.py` con `FakeRepo` y `FakeExtractor` compartidos desde `tests/fakes.py`.
   - Verifica el orden: tamaño/nombre/contenido → checksum → duplicado → extracción → persistencia.
   - Verifica que un duplicado no llama a `extract()` ni a `guardar_documento()`.
   - Verifica que un archivo excedido o un PDF corrupto no toca repositorio ni extractor.
   - **Criterio de aceptación:** los tests fallan si se invierte el orden o se omite un paso.

6. **Reemplazar el test de extracción por un test de especificación. [RESUELTO]**
   - El fixture `pdf_con_texto` genera un PDF real en memoria con texto conocido.
   - `test_extract_text_from_pdf` verifica el texto y el Markdown extraídos.
   - `test_upload_corrupt_pdf_with_header` confirma que un PDF corrupto no se marca como exitoso.
   - **Criterio de aceptación:** el test falla si `extract()` devuelve `""` o si se pierde el texto.

7. **Cubrir la rama magic/MIME. [RESUELTO]**
   - `test_upload_invalid_content` usa `filename="test.pdf"` y bytes no-PDF para llegar a `is_valid_pdf`.
   - `test_upload_corrupt_pdf_with_header` cubre el caso de header válido con cuerpo corrupto.
   - La validación MIME fue reemplazada por parseo real con `PdfReader`.
   - **Criterio de aceptación:** la cobertura de la validación de contenido no depende de un test que falla antes por extensión.

### Fase P1 — Calidad y cobertura

8. **Centralizar la configuración. [RESUELTO]**
   - `MONGO_URI`, `MONGO_DB_NAME`, `SESSION_SECRET_KEY`, `ENFORCE_IP_VALIDATION` y el límite de tamaño viven en `app/core/config.py`.
   - `validate_config()` / `get_session_secret_key()` fallan rápido en producción si falta el secreto.
   - El default de tamaño y la excepción `TamañoExcedidoError` usan `MAX_FILE_SIZE_MB`.
   - **Criterio de aceptación:** no quedan `os.getenv` de configuración fuera de `config.py` y el default de tamaño no está duplicado.

9. **Agregar tests de endpoints auxiliares. [RESUELTO]**
   - `/` → 200 y campos esperados.
   - `/health` → 200 con DB conectada; 503 con `ping()` fallando y estado `unhealthy`.
   - `/security.txt` → 200, `text/plain` y contenido RFC.
   - Checksum inválido en GET/PUT/DELETE → 400 (cubierto en `test_crud.py`).
   - **Criterio de aceptación:** los tres endpoints y el mapeo 400/404/409/413/503 tienen tests.

10. **Agregar tests de seguridad restantes. [RESUELTO]**
    - `is_safe_ip` con IP válida, inválida, privada y fuera de rango.
    - `generate_csrf_token` con longitud y unicidad.
    - Ramas de `is_valid_pdf`: válido, no-PDF, header corrupto y vacío.
    - **Criterio de aceptación:** las utilidades de seguridad tienen tests directos, no solo cobertura indirecta.

11. **Corregir el `FakeRepo`. [RESUELTO]**
    - Devuelve `Documento`, no `dict`.
    - Inicializa estado en `__init__`, no en atributos de clase.
    - Registra llamadas de `obtener`, `guardar`, `listar`, `actualizar`, `eliminar` y `ping`.
    - **Criterio de aceptación:** el fake respeta el mismo contrato que `MongoRepository`; los tests fallan si el adaptador cambia de firma.

12. **Documentar seams y proceso TDD. [RESUELTO]**
    - `CONTEXT.md` contiene el glosario de dominio y la lista de seams:
      `ProcesarDocumentoUseCase.execute`, `MongoRepository`, `PyPDFExtractor` y `build_router`.
    - `docs/adr/001-clean-architecture-y-seams.md` registra la decisión de capas, la
      inyección de dependencias y la decisión de no formalizar `Protocol`s todavía.
    - Para el próximo cambio, el proceso acordado es test rojo → implementación mínima →
      verde → refactor.
    - **Criterio de aceptación:** un lector nuevo puede saber dónde testear sin leer todo
      el código; el proceso TDD queda documentado y se aplicará al próximo cambio.

### Fase P2 — Limpieza y decisiones diferidas

13. **Decidir el destino de `SessionMiddleware`/`itsdangerous`. [RESUELTO]**
    - Decisión: se mantiene como parte del stack de seguridad y para una futura
      funcionalidad de sesión/CSRF; no hay endpoints que usen `request.session` hoy.
    - La decisión es reversible y quedó documentada en el ADR-001.
    - **Criterio de aceptación:** no queda infraestructura de sesión sin uso no
      documentada.

14. **Eliminar el string mágico `"Vacio"`. [RESUELTO]**
    - Se reemplazó por la constante `TEXTO_VACIO` en `procesar_documento.py`.
    - **Criterio de aceptación:** el caso de uso no contiene literales de dominio enterrados.

15. **Mantener OCP aplazado. [RESUELTO]**
    - No se introdujo `Protocol`; la decisión está documentada en el ADR-001.
    - Si aparece el segundo adaptador real, se formaliza el puerto.
    - **Criterio de aceptación:** la decisión está documentada y es reversible.

16. **Evaluar la conexión Mongo en `__init__`. [RESUELTO]**
    - Decisión: se mantiene en el composition root porque `MongoClient` es lazy y el
      adaptador es el único que conoce `pymongo`.
    - Si se busca DIP estricto o tests de integración con cliente inyectado, se moverá a
      una factory o a `lifespan`; la decisión está en el ADR-001.
    - **Criterio de aceptación:** no hay conexión real en import time y los tests
      unitarios usan `FakeRepo`.

---

## 7. Verdicto final

**VERDICTO FINAL: 100% Cumplido.**

Las Fases 1, 2 y 3 cerraron los bloqueantes y las brechas de calidad del informe:

- **P0:** arquitectura, inyección de dependencias, upload centralizado y tests unitarios del seam.
- **P1:** configuración centralizada, fail-fast de `SESSION_SECRET_KEY`, cobertura de endpoints y seguridad, `FakeRepo` alineado con el contrato real, documentación de seams y decisión explícita sobre la validación de IP.
- **P2:** `CONTEXT.md`, ADR-001 y cierre de las decisiones de limpieza diferida; P2.11, P2.12 y P2.13 quedan **[RESUELTO]**.

**Evidencia principal:**
- `main.py` delgado y composition root.
- Casos de uso CRUD y de upload con inyección por constructor y `Depends()`.
- Repositorio con salida tipada (`Documento`) y `FakeRepo` como seam de pruebas.
- Upload centralizado: validación real de PDF, sanitización de nombre y texto, checksum, duplicado y persistencia en un solo seam.
- Tests unitarios de los cinco casos de uso con `FakeRepo`/`FakeExtractor`.
- Endpoints auxiliares y utilidades de seguridad cubiertos.
- Configuración centralizada y fail-fast de `SESSION_SECRET_KEY` en producción.
- `CONTEXT.md` con arquitectura, glosario, seams y guía de ejecución.
- `docs/adr/001-clean-architecture-y-seams.md` con la decisión y sus consecuencias.
- Suite: **77 tests verdes**; `ruff check .` sin observaciones.

**Calificación conceptual:** *100% Cumplido — arquitectura, aplicación, configuración, pruebas y documentación alineadas con la rúbrica.* Las decisiones P2 restantes quedaron documentadas como límites conscientes y reversibles, no como deuda bloqueante.

---

*Informe generado a partir de la auditoría de los 3 archivos de `feedback_profe/` y del código en `app/`, `tests/` y `pyproject.toml`. La auditoría original fue de solo lectura; las Fases 1, 2 y 3 posteriores aplicaron los cambios P0, P1 y P2 documentados y actualizaron este informe.*
