import io
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from app.services.pdf_extractor import PyPDFExtractor
from app.database import MongoRepository

app = FastAPI(
    title="Extractor de PDF - UTN San Rafael",
    description="""
    API para la Etapa 1.
    Cumple con extracción en RAM, validación de formato/tamaño, generación de Checksum,
    persistencia en MongoDB sin duplicados y operaciones CRUD completas.
    """,
    version="1.2.0"
)

extractor = PyPDFExtractor()
db = MongoRepository()

# Definimos el tamaño máximo: 5 Megabytes (en bytes)
MAX_FILE_SIZE = 5 * 1024 * 1024 

@app.get("/", tags=["Estado"])
def root():
    return {"status": "online", "message": "API Extractor de PDF lista y conectada a MongoDB"}

# =====================================================================
# C - CREATE (Subir y Procesar PDF)
# =====================================================================
@app.post("/upload", tags=["Documentos (CRUD)"], summary="1. Crear: Subir PDF y guardar")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Recibe un PDF, valida formato y tamaño, verifica que no esté duplicado en la base de datos, 
    extrae su texto y lo guarda en MongoDB.
    """
    # 1. Validación de formato
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Error: El archivo proporcionado no es PDF.")

    # 2. Validación de tamaño (Máx 5MB)
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Error: El archivo supera los 5MB.")

    try:
        # Lectura en RAM
        contents = await file.read()
        archivo_en_ram = io.BytesIO(contents)

        # 3. Generación de Checksum ANTES de guardar
        checksum = extractor.calculate_checksum(archivo_en_ram)

        # 4. Rúbrica: "El documento no debe existir duplicado"
        if db.obtener_por_checksum(checksum):
            raise HTTPException(
                status_code=409, 
                detail="Error Conflicto: Este PDF ya fue procesado y existe en la base de datos."
            )

        # 5. Capa de Negocio y Guardado
        texto_extraido = extractor.extract(archivo_en_ram)
        db.guardar_documento(file.filename, texto_extraido if texto_extraido else "Vacio", checksum)

        return {
            "status": "success",
            "message": "Documento procesado y guardado correctamente.",
            "filename": file.filename,
            "sha256": checksum
        }

    except HTTPException as he:
        raise he # Dejamos pasar los errores 400 y 409 limpios
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error crítico del servidor: {str(e)}")

# =====================================================================
# R - READ (Leer documentos persistidos)
# =====================================================================
@app.get("/documentos", tags=["Documentos (CRUD)"], summary="2. Leer: Listar todos los PDFs")
def listar_documentos():
    """Devuelve una lista con todos los documentos procesados hasta ahora."""
    return {"total": len(db.listar_todos()), "documentos": db.listar_todos()}

@app.get("/documentos/{checksum}", tags=["Documentos (CRUD)"], summary="2. Leer: Buscar por Hash")
def obtener_documento(checksum: str):
    """Busca un documento específico utilizando su hash SHA-256."""
    doc = db.obtener_por_checksum(checksum)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    
    doc.pop("_id", None) # Limpiamos el ID interno de Mongo para que la respuesta sea más limpia
    return doc

# =====================================================================
# U - UPDATE (Actualizar información)
# =====================================================================
@app.put("/documentos/{checksum}", tags=["Documentos (CRUD)"], summary="3. Actualizar: Modificar nombre")
def actualizar_documento(checksum: str, nuevo_nombre: str = Body(embed=True)):
    """Permite corregir el nombre de un archivo que ya fue guardado en la base de datos."""
    if not db.obtener_por_checksum(checksum):
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    
    # Actualizamos directamente usando la colección de Pymongo
    db.coleccion.update_one(
        {"hash_seguridad": checksum}, 
        {"$set": {"archivo": nuevo_nombre}}
    )
    return {"status": "success", "message": f"Nombre actualizado a: {nuevo_nombre}"}

# =====================================================================
# D - DELETE (Borrar documento)
# =====================================================================
@app.delete("/documentos/{checksum}", tags=["Documentos (CRUD)"], summary="4. Borrar: Eliminar PDF")
def borrar_documento(checksum: str):
    """Elimina permanentemente un registro de la base de datos."""
    if not db.obtener_por_checksum(checksum):
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    
    db.coleccion.delete_one({"hash_seguridad": checksum})
    return {"status": "success", "message": "Documento eliminado de la base de datos."}