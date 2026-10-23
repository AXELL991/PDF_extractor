# Análisis Clean Code — DRY · KISS · YAGNI · SOLID — PDF Extractor UTN

**Fecha:** 2026-08-18
**Alcance:** `app/` (521 líneas en `main.py`), `tests/`, `pyproject.toml`
**Criterio:** Principios de *Clean Code* de Robert C. Martin, verificados contra evidencia con referencias `archivo:línea`.

---

## 1. Resumen ejecutivo

El código es **legible y pequeño por módulo, pero incumple tres de los cuatro principios** evaluados con evidencia concreta:

| Principio | Verdicto | Evidencia principal |
|---|---|---|
| **DRY** | ⚠️ Parcial | Validación de tamaño copiada 3 veces; límite definido en 2 módulos; patrón "buscar o 404" repetido en 3 endpoints |
| **KISS** | ⚠️ Parcial | `main.py` hace demasiado (521 líneas, 6 responsabilidades); sobre-ingeniería de seguridad sin uso |
| **YAGNI** | ❌ Incumplido | ~18 dependencias declaradas sin usar; 9 funciones/DTOs muertos; 2 imports sin uso |
| **SOLID** | ⚠️ Parcial | SRP y DIP incumplidos; OCP incumplido de facto; LSP y ISP cumplidos |

El peor infractor es el **módulo `app/main.py`**: concentra presentación HTTP, orquestación de negocio, ensamblado de la app, middleware, mapeo de errores y helpers de dominio. Es la misma conclusión del informe de arquitectura (`analisis-arquitectura.md`, sección 5, C2).

---

## 2. Metodología

- Verificación estática manual de cada principio con grep dirigido por símbolo (funciones, imports, constantes).
- Criterio **DRY**: una regla, una implementación. **KISS**: complejidad mínima que satisface la rúbrica. **YAGNI**: nada que no se use hoy. **SOLID**: las 5 letras evaluadas por separado.
- Nota de contexto: `uv run pytest` no colecta hoy (`ModuleNotFoundError: No module named 'itsdangerous'`, ausente de `uv.lock`); cualquier refactor deberá dejar la suite verde primero.

---

## 3. DRY — Don't Repeat Yourself

**Verdicto: ⚠️ Parcial.** Hay repetición real de lógica y de configuración.

### 3.1 Validación de tamaño: 3 copias, una sola debería existir

La regla "el archivo no debe exceder `MAX_FILE_SIZE_BYTES`" está implementada **tres veces** en `main.py`, con el `raise TamañoExcedidoError` duplicado inline:

- `main.py:339–342` — check sobre `file.size`.
- `main.py:358–361` — check sobre `len(contents)` tras leer.
- `main.py:400–404` — `validar_tamaño()`, **definida y nunca llamada**.

Además, **la constante se define dos veces** en módulos distintos:

- `main.py:89–90` → `MAX_FILE_SIZE_MB` / `MAX_FILE_SIZE_BYTES`
- `app/core/security.py:29–30` → `MAX_CONTENT_LENGTH_MB` / `MAX_FILE_SIZE_BYTES`

Dos fuentes de verdad para el mismo límite = futuro bug garantizado (cambiar uno y olvidar el otro). Además el valor default está en 3 lugares (`main.py:89`, `security.py:29`, `exceptions.py:20`).

### 3.2 Patrón "buscar documento o 404" repetido en 3 endpoints

El mismo paso — `validate_checksum(checksum)` → `db.obtener_por_checksum()` → si no existe `raise DocumentoNoEncontradoError` — está repetido en:

- GET `obtener_documento` → `main.py:441–449`
- PUT `actualizar_documento` → `main.py:470–477`
- DELETE `borrar_documento` → `main.py:506–513`

Tres copias del mismo contrato de error. Si mañana el error 404 cambia de mensaje o de status, hay que tocarlo 3 veces.

### 3.3 Mismo dato, dos formas de ocultarlo

El `_id` de Mongo se trata de dos maneras distintas según el endpoint:

- `main.py:451` → `doc.pop("_id", None)` (borrado post-lectura).
- `database.py:46` → `listar_todos()` con `{"_id": 0}` (proyección pre-lectura).

Dos mecanismos para el mismo objetivo: conocimiento de Mongo filtrado a la capa HTTP.

**Corrección mínima:** una sola función de validación de tamaño reutilizable (p. ej. usar `validar_tamaño`, o moverla al caso de uso de C1), una sola constante (`app/core/security.py` como fuente única o un módulo `config`), y un helper `obtener_o_404(checksum)` (o que el repositorio devuelva un `Documento` tipado — ver `analisis-arquitectura.md` C3).

---

## 4. KISS — Keep It Simple, Stupid

**Verdicto: ⚠️ Parcial.** La lógica de dominio es simple y directa; el problema es que el módulo principal concentra demasiadas responsabilidades y hay sobre-ingeniería sin uso.

### 4.1 `main.py` hace demasiado (521 líneas, 6 preocupaciones)

El módulo es a la vez: ensamblado de la app (`57–172`), middleware (`178–224`), rutas HTTP (`255–521`), orquestación de negocio (`331–390`), helpers de dominio (`393–411`) y mapeo de errores (`237–249`). Un mantenedor no puede entender `upload_pdf` sin leer el 100% del archivo. Viola el **Stepdown Rule** (la narrativa no fluye de alto a bajo nivel: la orquestación de negocio está mezclada con el routing).

### 4.2 Complejidad defensiva que hoy no protege nada

- `app/core/security.py` declara funciones de hashing de contraseñas, HMAC, validación de IP, sanitización, magic numbers y CSRF en un mismo módulo; varias **nunca se usan** (ver YAGNI). Es complejidad que el lector paga sin recibir comportamiento.
- `main.py:197–203` — validación de IP por rango, condicionada a una env var que por defecto está apagada (`ENFORCE_IP_VALIDATION`), pero el costo de lectura ya está pagado.
- `main.py:161–172` — `try/except` que **traga** errores de configuración de `SessionMiddleware` ("Error configurando..." y sigue). Silenciar un fallo de seguridad es lo contrario de simple: el error se vuelve invisible.

### 4.3 `print()` en vez del logger

`app/services/pdf_extractor.py:20` usa `print(...)` para errores. El proyecto ya configura logging JSON rotativo (`core/logging_config.py`); el `print` rompe la observabilidad uniforme. Es el caso de "el framework de logging ya existe, úsalo".

**Corrección mínima:** separar `main.py` en adaptador HTTP + casos de uso (ver `analisis-arquitectura.md` C2), quitar el `try/except` que silencia, y sustituir `print` por `logger.error`.

---

## 5. YAGNI — You Aren't Gonna Need It

**Verdicto: ❌ Incumplido.** Es el principio con más evidencia objetiva.

### 5.1 ~18 dependencias declaradas sin un solo import

De las 30 dependencias de `pyproject.toml:7–38`, **ningún módulo importa**:

| Dependencia | Funcionalidad sugerida | Uso real |
|---|---|---|
| `requests`, `httpx` | Cliente HTTP / IA | — |
| `motor` | MongoDB async | se usa `pymongo` síncrono |
| `pydantic-settings`, `environs` | Configuración | se usa `os.getenv` |
| `python-jose`, `cryptography`, `bcrypt` | JWT / cripto / hashing | se usa `argon2` (y ni eso se invoca) |
| `pyotp` | 2FA | — |
| `structlog`, `python-json-logger` | Logging estructurado | hay `JSONFormatter` propio |
| `prometheus-fastapi-instrumentator` | Métricas | — |
| `watchdog` | Monitoreo de archivos | — |
| `secure` | Security headers | headers a mano en `main.py:91` |
| `werkzeug` | Utilidades de seguridad | — |
| `bandit` | Análisis estático | — |
| `starlette-context` | Trazabilidad | — |
| `python-certifi-win32` | Certificados | — |

La descripción de `pyproject.toml:4` habla de "resúmenes con IA" que no existen en el código. Cada dependencia es superficie de ataque y peso muerto de instalación.

### 5.2 9 funciones/DTOs/métodos muertos

| Símbolo | Ubicación | Estado |
|---|---|---|
| `validar_formato` | `main.py:393` | definida, nunca llamada |
| `validar_tamaño` | `main.py:400` | definida, nunca llamada |
| `hash_password` | `security.py:45` | definida, nunca llamada |
| `verify_password` | `security.py:50` | definida, nunca llamada |
| `generate_hmac` | `security.py:176` | definida, nunca llamada |
| `existe_documento` | `database.py:41` | definida, nunca llamada |
| `DocumentoResponse` | `dtos.py:5` | definida, nunca usada |
| `ListaDocumentosResponse` | `dtos.py:12` | definida, nunca usada |
| `PasswordHasher` (instancia) | `security.py:42` | instanciada para funciones muertas |

### 5.3 Imports y parámetros sin uso

- `import contextlib` (`main.py:19`) y `from typing import Any` (`main.py:24`) — sin uso.
- `Optional` en `dtos.py:2` — importado y sin uso.
- `validar_tamaño` recibe `UploadFile` y nunca se usa; la firma sugiere un plan de validación que se abandonó a mitad de camino (por eso la copia inline de `main.py:339`).

**Corrección mínima:** borrar símbolos muertos (el *test de borrado* es contundente: la complejidad desaparece, no se redistribuye), podar `pyproject.toml` a las ~10 dependencias usadas, y eliminar imports huérfanos (se puede verificar con `ruff` — ya está en dev-deps).

---

## 6. SOLID

### 6.1 S — Single Responsibility Principle

**❌ Incumplido.**

- `main.py` tiene al menos 6 responsabilidades (ver 4.1). Un cambio de regla de negocio obliga a tocar el mismo archivo que un cambio de CORS.
- `app/core/security.py` es un saco de funciones de seguridad sin cohesión: hashing de contraseñas, sanitización de filenames, validación de IP, magic numbers, CSRF, HMAC. Seis temas de seguridad en un solo módulo plano.
- `PyPDFExtractor` (`pdf_extractor.py`) mezcla dos responsabilidades: extraer texto y calcular checksum. Defendible como "procesar bytes de PDF", pero es la frontera más débil del paquete.

### 6.2 O — Open/Closed Principle

**❌ Incumplido de facto.**

- Para soportar un nuevo formato de archivo (p. ej. DOCX) o una nueva fuente de extracción, **no hay seam donde colgar una implementación nueva**: los módulos dependen de la clase concreta `PyPDFExtractor` instanciada en `main.py:230`. Añadir un formato = editar código existente, no extender.
- Lo mismo para las operaciones sobre documentos: sumar un caso de uso implica editar el mega-módulo HTTP.

### 6.3 L — Liskov Substitution Principle

**✅ Cumplido.**

- La jerarquía `DomainException` (`exceptions.py:4–34`) es coherente: las subclases sustituyen a la base sin cambiar el contrato (constructor, `message`, `status_code`). `test_exceptions.py` lo verifica (status 400/409/413/404, `str(exc)`).
- No hay herencia de comportamiento en otros módulos que pudiera romper sustitución.

### 6.4 I — Interface Segregation Principle

**✅ Cumplido (trivial).**

- No hay interfaces formales que violar; el único síntoma de interfaz mal segregada es el método muerto `existe_documento` (`database.py:41`) en una clase concreta usada por nadie más. Al introducir puertos (ver `analisis-arquitectura.md` C5), habrá que revisar que cada consumidor reciba solo lo que usa.

### 6.5 D — Dependency Inversion Principle

**❌ Incumplido.**

- El flujo de alto nivel (orquestar un upload) **depende de clases concretas**: `MongoRepository` y `PyPDFExtractor` se instancian directamente en `main.py:230–231` y se usan en los endpoints.
- El módulo HTTP (la capa más externa) depende simultáneamente de detalles de **FastAPI**, **pymongo** y **pypdf**. No hay ninguna abstracción intermedia: el alto nivel conoce la implementación concreta de todo lo que está debajo.
- "Acepta dependencias, no las crees": hoy los módulos crean sus dependencias (`MongoRepository.__init__` abre la conexión en `database.py:8–15`), lo que hace a los tests depender de parchear singletons (`tests/test_crud.py:14` `@patch("app.main.db")`).

---

## 7. Scorecard

| Principio | Cumplimiento | Evidencia | Prioridad de corrección |
|---|---|---|---|
| **DRY** | ⚠️ Parcial | 3 copias de validación de tamaño, 2 definiciones del límite, patrón 404 x3 | Alta |
| **KISS** | ⚠️ Parcial | `main.py` 6 responsabilidades; `try/except` que silencia; `print` en servicio | Alta |
| **YAGNI** | ❌ Incumplido | ~18 deps sin uso; 9 símbolos muertos; imports huérfanos | Alta (la más barata) |
| **SOLID — S** | ❌ | `main.py` + `security.py` multi-responsabilidad | Alta |
| **SOLID — O** | ❌ | Sin seam para nuevos formatos de archivo | Media |
| **SOLID — L** | ✅ | Jerarquía de excepciones coherente | — |
| **SOLID — I** | ✅ | Sin interfaces formales; único síntoma: método muerto | — |
| **SOLID — D** | ❌ | Alto nivel acoplado a `MongoRepository`/`PyPDFExtractor` concretos | Alta |

---

## 8. Plan de corrección priorizado

1. **YAGNI primero (costo casi nulo):** borrar las 9 funciones/DTOs/métodos muertos, los 2 imports huérfanos y podar `pyproject.toml` a dependencias con import real. Verificar con `ruff`.
2. **DRY:** unificar la validación de tamaño en una sola función (la `validar_tamaño` que ya existe), una sola fuente de verdad para `MAX_FILE_SIZE_BYTES`, y un helper `obtener_o_404` o un repositorio que devuelva `Documento` tipado.
3. **SRP + DIP (el de mayor impacto, coincide con el informe de arquitectura):** extraer el caso de uso `ProcesarDocumento` con interfaz `procesar_pdf(nombre, contenido) -> Resultado`, aceptando dependencias por parámetro. `main.py` queda como adaptador HTTP fino; los tests cruzan el seam del caso de uso sin parchear singletons.
4. **KISS:** mover el `print` de `pdf_extractor.py:20` a `logger.error`, y quitar el `try/except` silencioso de `main.py:161–172`.
5. **OCP (aplazado, ver `analisis-arquitectura.md` C5):** formalizar puertos solo cuando exista un segundo adaptador real ("un adaptador = seam hipotético; dos = seam real").

**Prerrequisito en todos los casos:** reparar la suite (`itsdangerous` ausente de `uv.lock`) para que cada refactor termine con `uv run pytest` en verde.

---

## 9. Conclusión

El código **funciona y es entendible línea a línea**, pero no es *clean*: DRY, YAGNI, SRP y DIP acumulan evidencia objetiva de violación, y la mayoría de las correcciones son de bajo riesgo y alto retorno. El problema estructural (un `main.py` que concentra seis responsabilidades y acopla el alto nivel a pymongo/pypdf) es el mismo que identifica `analisis-arquitectura.md`; atenderlo desde el caso de uso `ProcesarDocumento` resuelve DRY, SRP y DIP en un solo movimiento.

---

*Elaborado con la metodología del skill `clean-code` y el vocabulario de `codebase-design` (módulo, interfaz, seam, adaptador). Reporte de arquitectura complementario: `analisis-arquitectura.md`.*
