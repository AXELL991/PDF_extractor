# Análisis TDD — Cumplimiento de la disciplina — PDF Extractor UTN

**Fecha:** 2026-08-18
**Alcance:** `tests/` (23 tests), `app/`, historial de `git`, `pyproject.toml`
**Criterio:** Tres Leyes del TDD, "qué es un buen test", seams, y anti-patrones (acoplado a implementación, tautológico, slicing horizontal) del skill `tdd`.

---

## 1. Resumen ejecutivo

| Aspecto | Verdicto |
|---|---|
| **Tres Leyes del TDD** | ❌ No hay evidencia de red-before-green; el código de producción y los tests llegaron juntos, y los labels "TDD" son retroactivos |
| **Tests como especificación** | ⚠️ Parcial — 14 de 23 tests verifican comportamiento real; 1 es tautológico; varios verifican "forma" en vez de comportamiento |
| **Tests en seams** | ⚠️ Parcial — se testea en el seam HTTP y de clase, pero no hay seams pre-acordados documentados y el seam crítico (caso de uso) no existe |
| **Anti-patrones** | ❌ Presentes: test tautológico, mocks acoplados a implementación, tests de "forma" |
| **Suite ejecutable** | ❌ La suite **no corre hoy** (`ModuleNotFoundError: No module named 'itsdangerous'`) |

**Verdicto global: ❌ No cumple TDD como disciplina.** El proyecto tiene *tests* (23, organizados y razonables en su mayoría) pero no sigue el ciclo red → green → refactor: no hay evidencia de tests fallando primero, hay código muerto/especulativo (violación de la Ley 3), y la suite está rota.

---

## 2. Metodología y alcance

- Lectura completa de `tests/test_extractor_completo.py` (5), `tests/test_crud.py` (12), `tests/test_exceptions.py` (6) — 23 tests.
- Reconstrucción del historial de git para buscar evidencia del orden red-before-green.
- Ejecución de la suite para verificar el estado real (`uv run pytest --collect-only`).
- Verificación de imports/cruce de cobertura contra `app/`.

No existe `CONTEXT.md` ni ADRs: no hay un vocabulario de dominio escrito ni seams acordados por escrito, lo cual ya condiciona el análisis (el skill exige *confirmar los seams antes de escribir tests*).

---

## 3. Contexto: la suite no corre

```
uv run pytest --collect-only
E   ModuleNotFoundError: No module named 'itsdangerous'
ERROR tests/test_crud.py
!!! Interrupted: 1 error during collection !!!
11 tests collected, 1 error
```

`itsdangerous` (dependencia transitiva de Starlette/`SessionMiddleware`) no está en `uv.lock`; `test_crud.py` importa `app.main` y la colección aborta. **Un equipo que practica TDD no puede practicarlo con una suite que no arranca** — es el bloqueador número uno, previo a cualquier otra conclusión.

---

## 4. Las Tres Leyes del TDD — evidencia del historial

### Ley 1 — "No escribas código de producción sin un test que falle primero"

**No hay evidencia de que se cumpliera.** El commit que crea `main.py` con lógica de producción (`365c753`, 2026-04-08, *"feat: add main.py"*) **incluye también `tests/test_main.py` en el mismo commit**:

```
365c753 feat: add main.py
   main.py            | 83 +++++++++++
   tests/test_main.py | 26 +++++++++++
```

Los mensajes posteriores *etiquetan* el trabajo como TDD — `18ff8fc` (*"Estructura inicial: carpeta app, services y tests con TDD inicial"*), `738fe4c` (*"test: agregar suite de pruebas unitarias y de integración (TDD)"*) — pero son reorganizaciones retroactivas de archivos que ya existían, no ciclos red → green registrados.

Además, los primeros tests (hoy eliminados en el refactor `f49d61f`) eran de un tipo que el skill llama *slicing horizontal*: verificaban **la forma imaginada de las cosas**, no comportamiento:

```python
# tests/test_main.py (original, 365c753)
def test_pypdf_extractor_is_pdf_extractor_instance(self):
    extractor = PyPDFExtractor()
    assert isinstance(extractor, PDFExtractor)   # tautológico: el tipo contra sí mismo
```

### Ley 2 — "No escribas más test del suficiente para fallar"

**Parcial.** Los tests de excepciones y de checksum son mínimos y precisos. Los de CRUD, en cambio, cargan infraestructura (mocks del singleton, `TestClient`, decoradores) que excede lo necesario para fallar: verifican el *mapeo HTTP* de respuestas, no la orquestación que deberían proteger (ver sección 6).

### Ley 3 — "No escribas más código de producción del suficiente para pasar"

**❌ Incumplida.** La Ley 3 prohíbe anticipar funciones especulativas. El código contiene exactamente eso — funciones y módulos que ningún test exige:

| Código especulativo | Ubicación |
|---|---|
| `validar_formato`, `validar_tamaño` | `main.py:393,400` — nunca llamadas |
| `hash_password`, `verify_password`, `generate_hmac` | `security.py:45,50,176` — nunca llamadas |
| `existe_documento` | `database.py:41` — nunca llamada |
| `DocumentoResponse`, `ListaDocumentosResponse` | `dtos.py:5,12` — nunca usados |
| ~18 dependencias sin import (2FA, JWT, métricas, IA) | `pyproject.toml:7–38` — restos de una funcionalidad de resúmenes con IA que se eliminó (`f49d61f`) pero cuyas deps siguen |

Si los tests se hubieran escrito primero (Ley 1) y el código solo para pasarlos (Ley 3), nada de esto existiría.

---

## 5. ¿Qué es un buen test? Evaluación por archivo

### 5.1 `tests/test_exceptions.py` (6) — ✅ el más conforme

Tests unitarios limpios, con valores esperados independientes y literales:

- `test_domain_exception_base` (`:12`) — verifica `message`, `status_code`, `str()` con un caso concreto.
- `test_formato_invalido_error` (`:21`) — 400 y mensaje conocido.
- `test_tamaño_excedido_error_default` (`:28`) — 413 y "5MB".
- `test_tamaño_excedido_error_custom` (`:37`) — 10MB.
- `test_documento_duplicado_error` (`:44`) — 409.
- `test_documento_no_encontrado_error` (`:51`) — 404.

Lee como especificación del contrato de errores. **Sobrevive a refactors** porque no toca internals.

### 5.2 `tests/test_extractor_completo.py` (5) — ⚠️ mezcla bueno y malo

Buenos (valores esperados independientes):

- `test_calculate_checksum_returns_sha256` (`:18`) — 64 hex chars verificados con `int(checksum, 16)`. **Fuente de verdad independiente**: el formato SHA-256, no la implementación.
- `test_checksum_consistency` (`:30`) y `test_checksum_different_content` (`:42`) — propiedades del hash (mismo contenido → mismo hash; distinto → distinto).

**Tautológico** (el anti-patrón por definición del skill):

- `test_calculate_checksum_matches_hashlib` (`:54`):

```python
expected = hashlib.sha256(data).hexdigest()      # ← el test recalcula
actual   = extractor.calculate_checksum(content) # ← la impl usa hashlib.sha256(...).hexdigest()
assert actual == expected
```

El valor esperado se recalcula **exactamente igual** que la implementación (`pdf_extractor.py:27`). Este test **pasa por construcción** y nunca puede estar en desacuerdo con el código: es `expect(add(a, b)).toBe(a + b)`. El valor esperado debería ser un literal SHA-256 conocido (p. ej. el hash de un contenido fijo, calculado una vez por una herramienta externa).

**Test de "forma", no de comportamiento**:

- `test_extract_text_from_pdf` (`:8`) — solo `assert isinstance(resultado, str)`. Como `extract()` **traga todas las excepciones y devuelve `""`** (`pdf_extractor.py:18–21`), este test pasa incluso si la extracción estuviera completamente rota. Un test de especificación usaría un PDF real generado en memoria con texto conocido y verificaría el contenido extraído.

### 5.3 `tests/test_crud.py` (12) — ⚠️ buen contrato HTTP, mock acoplado

Positivo: verifica el **contrato HTTP** completo (422 sin archivo, 400 no-PDF, 409 duplicado, 404 inexistente, 200 success) — eso es comportamiento real de la superficie pública.

Negativo:

- **Todos parchean el singleton interno** `@patch("app.main.db")` (`:14, :40, :55, :66, :79, :95, :108, :122, :138, :150`). El test conoce el interior de `app.main` (el atributo `db`). Si `main.py` se refactoriza a inyección de dependencias **sin cambiar comportamiento, los tests se rompen** — el *tell* clásico del anti-patrón *implementation-coupled*.
- `test_upload_valid_pdf` (`:14`) nunca verifica que el PDF se procese de verdad: el contenido `b"%PDF-1.4 test content"` no es un PDF válido, la extracción devuelve `""` silenciosamente, y el test solo comprueba 200 + `"success"`. La **orquestación de 12 pasos** del upload (`main.py:331–390`) queda sin verificación de orden ni de omisión.
- La ruta de detección MIME (`security.py:135`, `magic.from_buffer`) **no está cubierta**: `test_upload_invalid_format` (`:32`) falla en el check de magic numbers antes de llegar al MIME.

---

## 6. Seams — dónde se testea y dónde debería testearse

El skill exige: *"Test only at pre-agreed seams … no test is written at an unconfirmed seam."*

**No hay seams acordados por escrito** (no hay `CONTEXT.md` ni ADR con la palabra "seam"). Los seams de facto son:

| Seam actual | Tests que lo cruzan | Evaluación |
|---|---|---|
| **HTTP** (`TestClient(app)`) | `test_crud.py` | Legítimo para integración del contrato, pero se cruza **junto con** parcheo de internals |
| **Clase** `PyPDFExtractor` | `test_extractor_completo.py` | Razonable; interface pequeña |
| **Clase** `DomainException` | `test_exceptions.py` | Correcto |

**El seam que falta.** La orquestación crítica (procesar un PDF: validar → checksum → deduplicar → extraer → sanitizar → persistir) no tiene interfaz propia porque vive inline en `upload_pdf`. No hay capa de aplicación donde apoyar un test — por eso los tests se ven forzados a parchear `app.main.db`. Crear el caso de uso `ProcesarDocumento` (ver `analisis-arquitectura.md` C1) crea el seam que hoy falta: los tests de CRUD pasarían a cruzar `procesar_pdf(nombre, contenido) -> Resultado` con adaptadores fake, sin HTTP ni singletons.

---

## 7. Anti-patrones detectados (resumen con evidencia)

| Anti-patrón | Evidencia | Dónde |
|---|---|---|
| **Tautológico** | El test recalcula el esperado con `hashlib`, la misma fuente que la implementación | `test_extractor_completo.py:54–60` |
| **Acoplado a implementación** | `@patch("app.main.db")` — el test alcanza el singleton interno del módulo | `test_crud.py` (11 parcheos) |
| **Tests de forma / slicing horizontal** | `isinstance(resultado, str)` pasa aunque la extracción esté rota; los tests originales verificaban `isinstance` de tipos entre sí | `test_extractor_completo.py:8–15`; `tests/test_main.py` histórico |
| **Verificar por canal lateral** (atenuado) | El health check toca `db.client` real; los tests no lo cubren, pero el patrón de alcanzar el cliente de Mongo existe | `main.py:293` |

---

## 8. Brechas de cobertura en rutas críticas

| Código crítico | ¿Directamente testeado? |
|---|---|
| `validate_file_content` (magic + MIME + tamaño) — `security.py:146` | Solo indirecto vía HTTP; la rama MIME (`magic`) nunca se ejecuta en tests |
| `sanitize_filename`, `sanitize_text`, `validate_checksum`, `is_valid_pdf`, `is_safe_ip` | ❌ Sin tests directos |
| Extracción con PDF real y texto conocido | ❌ Nunca se verifica contenido extraído |
| Endpoints `root`, `/health`, `/security.txt` | ❌ Sin tests |

Es notable: **el módulo de seguridad, el más sensible del sistema, es el menos probado directamente** — y es justo donde un test *tautológico* o *de forma* sería menos aceptable.

---

## 9. Scorecard TDD

| Criterio | Cumplimiento | Evidencia |
|---|---|---|
| Ley 1 — red before green | ❌ | `main.py` y tests en el mismo commit (`365c753`); labels TDD retroactivos |
| Ley 2 — tests mínimos | ⚠️ | Tests de excepciones/checksum mínimos; CRUD carga mocks de más |
| Ley 3 — código mínimo para pasar | ❌ | 9 funciones/DTOs muertos, ~18 deps especulativas |
| Tests como especificación | ⚠️ | 14/23 comportamentales; 1 tautológico; 1 de forma |
| Tests en seams pre-acordados | ❌ | Sin seams documentados; el seam crítico no existe |
| Sin anti-patrones | ❌ | Tautológico + acoplado a implementación + forma |
| Suite ejecutable (F.I.R.S.T. — "Fast", "Repeatable") | ❌ | `ModuleNotFoundError: itsdangerous` |

---

## 10. Plan de mejora

1. **Reparar la suite** — agregar `itsdangerous` a `uv.lock` (`uv add itsdangerous` o sync). Sin suite verde no hay ciclo posible.
2. **Arreglar el test tautológico** — reemplazar `hashlib.sha256(data).hexdigest()` por un literal SHA-256 conocido (calculado una vez con una herramienta externa o incluido como fixture documentada).
3. **Crear el seam que falta (C1 del análisis de arquitectura)** — extraer `ProcesarDocumento`; los tests de CRUD pasan de parchear `app.main.db` a inyectar adaptadores fake en el caso de uso. Esto elimina el anti-patrón de acoplamiento y verifica la orquestación completa.
4. **Convertir el test de extracción en especificación** — generar un PDF en memoria con `pypdf` (`PdfWriter`), escribir texto conocido y verificar que `extract()` lo devuelve.
5. **Testear el módulo de seguridad directamente** — tablas de casos para `sanitize_filename`, `validate_checksum`, `validate_file_content` (incluida la rama MIME).
6. **Eliminar el código especulativo (Ley 3)** — borrar funciones muertas y podar `pyproject.toml`, antes de añadir más tests.
7. **Practicar el ciclo de verdad a futuro** — para cada nueva capacidad: un test que falle → implementación mínima → ver. Documentar los seams en `CONTEXT.md`.

**Nota de proceso:** el skill `tdd` exige acordar los seams *antes* de escribir cada test. Una vez decidida la profundización (`ProcesarDocumento` o el módulo de seguridad), el siguiente paso es definir formalmente los seams a testear.

---

## 11. Conclusión

El proyecto **tiene tests, no practica TDD**. Hay 23 tests, organizados y con un contrato HTTP razonable, pero: no hay evidencia de red-before-green, la Ley 3 se viola con código especulativo, existe un test tautológico que "no puede fallar", los tests de CRUD están acoplados a la implementación (`app.main.db`), y la suite no corre en este entorno. La corrección de mayor impacto no es escribir más tests sino **crear el seam de caso de uso que falta** — igual que concluye `analisis-arquitectura.md` — para que los tests tengan un lugar donde observar la orquestación real sin conocer los internals del módulo HTTP.

---

*Elaborado con la metodología del skill `tdd` (Tres Leyes, seams, anti-patrones) y el vocabulario de `codebase-design`. Reportes complementarios: `analisis-arquitectura.md`, `analisis-clean-code.md`.*
