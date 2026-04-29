import io
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse

from app.services.pdf_extractor import PyPDFExtractor
from app.database import MongoRepository
from app.dtos import UploadResponse, MensajeResponse, ActualizarRequest
from app.exceptions import DomainException

app = FastAPI(
    title="Extractor de PDF - UTN San Rafael",
    description="""
    API para la Etapa 1.
    Cumple con extracción en RAM, validación de formato/tamaño, generación de Checksum,
    persistencia en MongoDB sin duplicados y operaciones CRUD completas.
    """,
    version="1.3.0"
)

extractor = PyPDFExtractor()
db = MongoRepository()

MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    """Maneja todas las excepciones del dominio de forma uniforme."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.get("/", tags=["Estado"])
def root():
    return {"status": "online", "message": "API Extractor de PDF lista y conectada a MongoDB"}


# =====================================================================
# C - CREATE (Subir y Procesar PDF)
# =====================================================================
@app.post("/upload", tags=["Documentos (CRUD)"], summary="1. Crear: Subir PDF y guardar")
async def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
    """
    Recibe un PDF, valida formato y tamaño, verifica que no esté duplicado,
    extrae su texto y lo guarda en MongoDB.
    """
    validar_formato(file.filename)
    await validar_tamaño(file)

    contents = await file.read()
    archivo_en_ram = io.BytesIO(contents)

    checksum = extractor.calculate_checksum(archivo_en_ram)
    verificar_duplicado(checksum)

    texto_extraido = extractor.extract(archivo_en_ram)
    db.guardar_documento(
        file.filename,
        texto_extraido if texto_extraido else "Vacio",
        checksum
    )

    return UploadResponse(
        status="success",
        message="Documento procesado y guardado correctamente.",
        filename=file.filename,
        sha256=checksum
    )


def validar_formato(filename: str):
    """Verifica que el archivo sea PDF."""
    if not filename.lower().endswith('.pdf'):
        from app.exceptions import FormatoInvalidoError
        raise FormatoInvalidoError()


async def validar_tamaño(file: UploadFile):
    """Verifica que el archivo no exceda el tamaño máximo."""
    if file.size and file.size > MAX_FILE_SIZE_BYTES:
        from app.exceptions import TamañoExcedidoError
        raise TamañoExcedidoError(MAX_FILE_SIZE_MB)


def verificar_duplicado(checksum: str):
    """Verifica que el documento no exista ya en la base de datos."""
    if db.obtener_por_checksum(checksum):
        from app.exceptions import DocumentoDuplicadoError
        raise DocumentoDuplicadoError()


# =====================================================================
# R - READ (Leer documentos persistidos)
# =====================================================================
@app.get("/documentos", tags=["Documentos (CRUD)"], summary="2. Leer: Listar todos los PDFs")
def listar_documentos():
    """Devuelve una lista con todos los documentos procesados hasta ahora."""
    documentos = db.listar_todos()
    return {"total": len(documentos), "documentos": documentos}


@app.get("/documentos/{checksum}", tags=["Documentos (CRUD)"], summary="2. Leer: Buscar por Hash")
def obtener_documento(checksum: str):
    """Busca un documento específico utilizando su hash SHA-256."""
    doc = db.obtener_por_checksum(checksum)
    if not doc:
        from app.exceptions import DocumentoNoEncontradoError
        raise DocumentoNoEncontradoError()
    doc.pop("_id", None)
    return doc


# =====================================================================
# U - UPDATE (Actualizar información)
# =====================================================================
@app.put("/documentos/{checksum}", tags=["Documentos (CRUD)"], summary="3. Actualizar: Modificar nombre")
def actualizar_documento(checksum: str, request: ActualizarRequest) -> MensajeResponse:
    """Permite corregir el nombre de un archivo que ya fue guardado."""
    if not db.obtener_por_checksum(checksum):
        from app.exceptions import DocumentoNoEncontradoError
        raise DocumentoNoEncontradoError()

    db.actualizar_nombre(checksum, request.nuevo_nombre)
    return MensajeResponse(
        status="success",
        message=f"Nombre actualizado a: {request.nuevo_nombre}"
    )


# =====================================================================
# D - DELETE (Borrar documento)
# =====================================================================
@app.delete("/documentos/{checksum}", tags=["Documentos (CRUD)"], summary="4. Borrar: Eliminar PDF")
def borrar_documento(checksum: str) -> MensajeResponse:
    """Elimina permanentemente un registro de la base de datos."""
    if not db.obtener_por_checksum(checksum):
        from app.exceptions import DocumentoNoEncontradoError
        raise DocumentoNoEncontradoError()

    db.eliminar_documento(checksum)
    return MensajeResponse(
        status="success",
        message="Documento eliminado de la base de datos."
    )
