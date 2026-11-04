"""Excepciones puras del dominio, sin referencias a HTTP o frameworks externos."""

DEFAULT_STATUS_CODE = 500


class DomainException(Exception):
    """Excepción base del dominio."""

    status_code = DEFAULT_STATUS_CODE

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DocumentoInvalidoError(DomainException):
    """El documento no cumple las invariantes de dominio."""

    status_code = 400

    def __init__(self, message: str = "Documento inválido."):
        super().__init__(message)


class FormatoInvalidoError(DomainException):
    """El archivo no es un PDF válido."""

    status_code = 400

    def __init__(self, message: str = "El archivo proporcionado no es PDF."):
        super().__init__(message)


class TamañoExcedidoError(DomainException):
    """El archivo supera el tamaño máximo permitido."""

    status_code = 413

    def __init__(self, message: str = "El archivo supera el tamaño máximo permitido."):
        super().__init__(message)


class DocumentoDuplicadoError(DomainException):
    """El documento ya existe en la base de datos."""

    status_code = 409

    def __init__(
        self, message: str = "Este PDF ya fue procesado y existe en la base de datos."
    ):
        super().__init__(message)


class DocumentoNoEncontradoError(DomainException):
    """El documento no fue encontrado."""

    status_code = 404

    def __init__(self, message: str = "Documento no encontrado."):
        super().__init__(message)


class ExtractionError(DomainException):
    """No se pudo extraer el contenido de un PDF válido."""

    status_code = 422

    def __init__(
        self,
        message: str = "No se pudo extraer el contenido del PDF.",
    ):
        super().__init__(message)


class ChecksumInvalidoError(DomainException):
    """El checksum recibido no tiene formato SHA-256."""

    status_code = 400

    def __init__(self, message: str = "El checksum debe ser un hash SHA-256 válido."):
        super().__init__(message)


class NombreArchivoInvalidoError(DomainException):
    """El nombre de archivo no cumple las reglas de seguridad."""

    status_code = 400

    def __init__(self, message: str = "Nombre de archivo inválido."):
        super().__init__(message)
