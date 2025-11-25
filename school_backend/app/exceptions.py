"""
Manejo centralizado de excepciones personalizadas.
"""
from fastapi import HTTPException, status


class SchoolBackendException(HTTPException):
    """Excepción base personalizada."""
    pass


class NotFoundError(SchoolBackendException):
    """Recurso no encontrado."""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} con ID {resource_id} no encontrado"
        )


class ConflictError(SchoolBackendException):
    """Conflicto de recursos (duplicado, etc.)."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class UnauthorizedError(SchoolBackendException):
    """No autorizado."""
    def __init__(self, detail: str = "No autorizado"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class ForbiddenError(SchoolBackendException):
    """Prohibido (sin permisos)."""
    def __init__(self, detail: str = "No tiene permisos para realizar esta acción"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ValidationError(SchoolBackendException):
    """Error de validación."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )

class InactiveUserError(SchoolBackendException):
    """Usuario inactivo."""
    def __init__(self, detail: str = "Usuario inactivo"):
        super().__init__(
            status_code=430,
            detail=detail
        )

