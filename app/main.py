from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse

from app.services.pdf_extractor import PyPDFExtractor
from app.database import MongoRepository
from app.dtos import UploadResponse, MensajeResponse, ActualizarRequest
from app.exceptions import DomainException
from app.use_cases.procesar_documento import ProcesarDocumentoUseCase

app = FastAPI(
    title="Extractor de PDF - UTN San Rafael",
    description="""
    API para la Etapa 1.
    Cumple con extracción en RAM, validación de formato/tamaño, generación de Checksum,
    persistencia en MongoDB sin duplicados y operaciones CRUD completas.
    """,
    version="1.4.0"
)

extractor = PyPDFExtractor()
db = MongoRepository()
procesar_doc_use_case = ProcesarDocumentoUseCase(extractor=extractor, db=db)


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
    contents = await file.read()
    # Se re-liga el repositorio del módulo para mantenerlo intercambiable (tests).
    procesar_doc_use_case.db = db
    return procesar_doc_use_case.execute(
        filename=file.filename,
        content_bytes=contents,
        file_size=file.size,
    )


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
