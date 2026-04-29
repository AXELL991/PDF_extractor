"""Excepciones personalizadas del dominio."""


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
    def __init__(self, max_size_mb: int = 5):
        message = f"El archivo supera los {max_size_mb}MB."
        super().__init__(message, status_code=413)


class DocumentoDuplicadoError(DomainException):
    """El documento ya existe en la base de datos."""
    def __init__(self, message: str = "Este PDF ya fue procesado y existe en la base de datos."):
        super().__init__(message, status_code=409)


class DocumentoNoEncontradoError(DomainException):
    """El documento no fue encontrado."""
    def __init__(self, message: str = "Documento no encontrado."):
        super().__init__(message, status_code=404)
