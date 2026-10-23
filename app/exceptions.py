"""Excepciones personalizadas del dominio."""

from app.core.config import MAX_FILE_SIZE_MB


class DomainException(Exception):
    """Excepcion base del dominio."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class FormatoInvalidoError(DomainException):
    """El archivo no es un PDF valido."""

    def __init__(self, message: str = "El archivo proporcionado no es PDF."):
        super().__init__(message, status_code=400)


class TamañoExcedidoError(DomainException):
    """El archivo supera el tamaño maximo permitido."""

    def __init__(self, max_size_mb: int | None = None):
        limite = MAX_FILE_SIZE_MB if max_size_mb is None else max_size_mb
        message = f"El archivo supera los {limite}MB."
        super().__init__(message, status_code=413)


class DocumentoDuplicadoError(DomainException):
    """El documento ya existe en la base de datos."""

    def __init__(
        self, message: str = "Este PDF ya fue procesado y existe en la base de datos."
    ):
        super().__init__(message, status_code=409)


class DocumentoNoEncontradoError(DomainException):
    """El documento no fue encontrado."""

    def __init__(self, message: str = "Documento no encontrado."):
        super().__init__(message, status_code=404)


class ExtractionError(DomainException):
    """No se pudo extraer el contenido de un PDF válido."""

    def __init__(
        self,
        message: str = "No se pudo extraer el contenido del PDF.",
    ):
        super().__init__(message, status_code=422)


class ChecksumInvalidoError(DomainException):
    """El checksum recibido no tiene formato SHA-256."""

    def __init__(self, message: str = "El checksum debe ser un hash SHA-256 válido."):
        super().__init__(message, status_code=400)


class NombreArchivoInvalidoError(DomainException):
    """El nombre de archivo no cumple las reglas de seguridad."""

    def __init__(self, message: str = "Nombre de archivo inválido."):
        super().__init__(message, status_code=400)
