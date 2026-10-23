# ADR-001: Adopción de Clean Architecture, Inyección de Dependencias y Fakes para Pruebas Unitarias

- **Estado:** Aceptado
- **Fecha:** 23/10/2026
- **Proyecto:** PDF Extractor & Document Management API — UTN FRSR
- **Decisores:** Equipo de desarrollo
- **Ámbito:** Arquitectura de la aplicación, estrategia de pruebas y puntos de extensión

---

## 1. Contexto

La API nació con una estructura en la que `app/main.py` concentraba la creación de la
app FastAPI, los middlewares, las rutas, la orquestación del upload y el acceso directo
a MongoDB. Esa concentración producía varios problemas:

- los controladores HTTP conocían detalles de persistencia y de `pypdf`;
- la orquestación crítica del upload no tenía una interfaz propia y solo se probaba a
  través de HTTP;
- los tests parcheaban el singleton `app.main.db`, acoplándose a la implementación;
- la configuración estaba dispersa en varios módulos;
- no existía documentación escrita de los seams ni de las decisiones de arquitectura.

La cátedra exige aplicar los principios de **Clean Architecture** y **SOLID**, en
particular la separación de responsabilidades y el **Principio de Inversión de
Dependencias (DIP)**. También exige que los tests se apoyen en seams acordados y que la
suite sea rápida y repetible.

El objetivo de esta decisión es desacoplar la presentación de la infraestructura,
centralizar la lógica de aplicación y hacer explícitos los puntos de sustitución que ya
se usan en los tests.

---

## 2. Decisión

Se adopta la siguiente arquitectura y estrategia de pruebas.

### 2.1 Separación en capas

| Capa | Contenido | Regla |
|---|---|---|
| **Dominio** | `Documento`, DTOs y excepciones de negocio. | No importa FastAPI, MongoDB ni `pypdf`. |
| **Aplicación / casos de uso** | `ProcesarDocumentoUseCase` y los cuatro casos de uso CRUD. | Orquestan reglas y dependen de colaboradores inyectados. |
| **Infraestructura** | `MongoRepository`, `PyPDFExtractor`, configuración y seguridad. | Implementan detalles reemplazables. |
| **Presentación** | `app/main.py`, rutas, dependencias, middlewares y handlers. | Traducen HTTP ↔ casos de uso; no contienen reglas de negocio. |

La dirección de dependencias va desde presentación/infraestructura hacia aplicación y
dominio. La presentación no importa `pymongo` ni usa `pypdf` directamente.

### 2.2 Casos de uso como seam de aplicación

La orquestación del upload se extrae a:

```python
ProcesarDocumentoUseCase.execute(
    filename: str,
    content_bytes: bytes,
    file_size: int | None = None,
) -> UploadResponse
```

El caso de uso concentra, en orden:

1. validación de tamaño;
2. sanitización y validación del nombre;
3. validación real del PDF;
4. cálculo de checksum;
5. verificación de duplicado;
6. extracción a Markdown;
7. sanitización del texto;
8. persistencia.

Los casos de uso CRUD (`Listar`, `Obtener`, `Actualizar`, `Eliminar`) validan el checksum
y la existencia del documento, y delegan la persistencia en el repositorio.

### 2.3 Inyección de dependencias

`app/main.py` actúa como **composition root**:

- crea `MongoRepository` y `PyPDFExtractor`;
- los publica en `app.state`;
- `app/api/dependencies.py` los obtiene con `Depends()` y construye los casos de uso
  por request.

No se usa un singleton global de base de datos dentro de las rutas ni se mutan
instancias compartidas de casos de uso. Esto permite sustituir los adaptadores sin
tocar los controladores.

### 2.4 `FakeRepo` como seam de pruebas

Se adopta un `FakeRepo` en memoria como adaptador de test del contrato de persistencia.
El fake:

- almacena objetos `Documento`, no diccionarios crudos;
- implementa `obtener_por_checksum`, `guardar_documento`, `listar_todos`,
  `actualizar_nombre`, `eliminar_documento` y `ping`;
- registra el orden de las llamadas y permite verificar efectos secundarios;
- se complementa con `FakeExtractor`, que permite controlar checksum y texto extraído.

Los tests unitarios cruzan el seam del caso de uso con estos fakes, sin HTTP, sin
MongoDB y sin archivos. Los tests de contrato HTTP usan `TestClient` y publican el fake
en `app.state.repositorio`, que es el mismo seam que usa el composition root.

### 2.5 Configuración centralizada

Toda la configuración de entorno se centraliza en `app/core/config.py`. `app/main.py`
valida al arrancar y falla rápido si el límite de tamaño no es válido. El límite tiene
una única fuente: `MAX_FILE_SIZE_MB` / `MAX_FILE_SIZE_BYTES`.

### 2.6 Decisiones diferidas y límites conscientes

- **No se formalizan `Protocol`s todavía.** El caso de uso usa tipos concretos
  (`MongoRepository`, `PyPDFExtractor`) porque aún no existe un segundo adaptador real
  que justifique un puerto formal. Se aplica YAGNI/OCP diferido. Si aparece otro motor
  de base de datos u otro extractor, se introduce el `Protocol` y se ajusta la
  inyección.
- **`MongoRepository.__init__` crea el cliente.** `MongoClient` es lazy y el composition
  root es el lugar previsto para construir el adaptador. Si se busca DIP estricto o se
  necesita testear el adaptador con un cliente inyectado, se moverá a una factory o a
  `lifespan`.
---

## 3. Consecuencias

### 3.1 Positivas

- **Independencia de la base de datos:** los casos de uso y los tests no conocen
  `pymongo`; se puede sustituir MongoDB por otro adaptador sin reescribir la lógica.
- **Pruebas unitarias ultrarrápidas y aisladas de I/O:** `FakeRepo`/`FakeExtractor`
  permiten verificar orden, duplicados, validaciones y efectos secundarios sin red ni
  disco.
- **Cumplimiento de DIP:** la capa de aplicación recibe sus colaboradores; la
  presentación no construye ni conoce la infraestructura concreta.
- **Mayor localidad:** cada regla vive en un caso de uso y cada detalle técnico en su
  adaptador.
- **Contrato HTTP estable:** los handlers quedan finos y los errores de dominio se
  traducen de forma uniforme.
- **Configuración predecible:** un único módulo concentra el entorno y el arranque de
  producción falla rápido ante una configuración incompleta.

### 3.2 Negativas / trade-offs

- Hay más archivos y una indirección adicional entre ruta y persistencia.
- Los casos de uso siguen dependiendo de tipos concretos; formalizar puertos con
  `Protocol` se difiere hasta que exista un segundo adaptador real.
- El `FakeRepo` debe mantenerse sincronizado con el contrato de `MongoRepository`.
- La suite unitaria no reemplaza una prueba de integración contra MongoDB real; esa
  verificación queda fuera del alcance de la suite rápida.

### 3.3 Neutrales

- El texto vacío se representa con la constante `TEXTO_VACIO` en la capa de aplicación;
  puede evolucionar a un estado explícito sin afectar los seams.

---

## 4. Alternativas consideradas

1. **Mantener toda la lógica en `main.py` y probar solo por HTTP.**
   Descartada: acopla los tests a FastAPI y al singleton de MongoDB, y no permite
   verificar la orquestación de forma aislada.

2. **Usar mocks de `pymongo` en los tests.**
   Descartada: reproduce detalles del driver, es frágil y no especifica el contrato de
   dominio. El `FakeRepo` expresa mejor la interfaz que consume la aplicación.

3. **Introducir `Protocol`s y puertos formales de inmediato.**
   Diferida: no hay un segundo adaptador real. La complejidad no se justifica todavía;
   la decisión queda documentada para cuando aparezca.

4. **Confiar en `X-Forwarded-For` sin validar el proxy.**
   Descartada: permite spoofing de IP. Se mantiene la validación opt-in y se documenta
   su alcance.

---

## 5. Verificación

- `uv run pytest -q` → **77 tests en verde**.
- `uv run ruff check .` → **All checks passed!**
- `tests/test_use_cases.py` verifica el seam de aplicación y los casos borde.
- `tests/test_crud.py` verifica el contrato HTTP con `FakeRepo`.
- `tests/test_auxiliary_routes.py` cubre `/`, `/health` y `/security.txt`.
- `tests/test_config.py` cubre la configuración centralizada y el fail-fast de
  producción.

---

## 6. Referencias

- `CONTEXT.md` — mapa de arquitectura, glosario, seams y guía de ejecución.
- `app/use_cases/procesar_documento.py` — caso de uso de upload.
- `app/use_cases/gestionar_documentos.py` — casos de uso CRUD.
- `app/api/dependencies.py` — inyección con `Depends()`.
- `app/database.py` — adaptador MongoDB.
- `app/services/pdf_extractor.py` — adaptador de extracción.
- `tests/fakes.py` — `FakeRepo` y `FakeExtractor`.
- `AUDITORIA_PROFE.md` — estado final y trazabilidad de hallazgos.
