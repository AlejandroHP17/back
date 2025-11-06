"""
Schemas para respuestas genéricas de la API.
"""
from typing import TypeVar, Generic, Optional, List
from pydantic import BaseModel, Field, ConfigDict
from fastapi import status

# Tipo genérico para los datos de la respuesta
T = TypeVar('T')


class Response(BaseModel):
    """Modelo para la respuesta con código y mensaje."""
    code: int = Field(..., description="Código de estado HTTP del servicio")
    message: str = Field(..., description="Mensaje descriptivo de la operación")


class GenericResponse(BaseModel, Generic[T]):
    """Modelo genérico para todas las respuestas de la API."""
    data: T = Field(..., description="Datos de la respuesta")
    response: Response = Field(..., description="Información de la respuesta (código y mensaje)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {},
                "response": {
                    "code": 200,
                    "message": "Éxito"
                }
            }
        }
    )


# Funciones helper para generar respuestas exitosas
def success_response(
    data: T,
    code: int = status.HTTP_200_OK,
    message: str = "Éxito"
) -> GenericResponse[T]:
    """
    Genera una respuesta exitosa.
    
    Args:
        data: Los datos a retornar
        code: Código HTTP de éxito (default: 200)
        message: Mensaje de éxito (default: "Éxito")
    
    Returns:
        GenericResponse con los datos y respuesta exitosa
    """
    return GenericResponse(
        data=data,
        response=Response(code=code, message=message)
    )


def created_response(
    data: T,
    message: str = "Éxito"
) -> GenericResponse[T]:
    """
    Genera una respuesta de creación exitosa (201).
    
    Args:
        data: Los datos a retornar
        message: Mensaje de éxito (default: "Éxito")
    
    Returns:
        GenericResponse con código 201
    """
    return success_response(data=data, code=status.HTTP_201_CREATED, message=message)


def get_error_message(status_code: int, error_detail: str = "") -> str:
    """
    Obtiene el mensaje de error apropiado según el código de estado HTTP.
    
    Args:
        status_code: Código de estado HTTP
        error_detail: Detalle adicional del error (opcional)
    
    Returns:
        Mensaje descriptivo del error
    """
    error_messages = {
        status.HTTP_400_BAD_REQUEST: "Solicitud inválida",
        status.HTTP_401_UNAUTHORIZED: "No autorizado",
        status.HTTP_403_FORBIDDEN: "Acceso prohibido",
        status.HTTP_404_NOT_FOUND: "Recurso no encontrado",
        status.HTTP_409_CONFLICT: "Conflicto",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "Error de validación",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "Error interno del servidor",
    }
    
    message = error_messages.get(status_code, "Error en la solicitud")
    
    # Si hay un detalle adicional, agregarlo al mensaje
    if error_detail:
        message = f"{message}: {error_detail}"
    
    return message

