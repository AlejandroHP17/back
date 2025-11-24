"""
Schemas para respuesta detallada.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from decimal import Decimal
from app.schemas.work_type import WorkTypeResponse


class WorkTypeDetailResponse(BaseModel):
    """Schema para tipo de trabajo con peso de evaluación."""
    work_type_id: int = Field(..., description="ID del tipo de trabajo")
    work_type_name: str = Field(..., description="Nombre del tipo de trabajo")
    evaluation_weight: Decimal = Field(..., description="Peso de evaluación (porcentaje)")
    
    model_config = ConfigDict(from_attributes=True)

class WorkTypeDetail(BaseModel):
    """Schema para tipo de trabajo con peso de evaluación."""
    formative_field_id: int = Field(..., description="ID del campo formativo")
    formative_field_name: str = Field(..., description="Nombre del campo formativo")
    work_types: List[WorkTypeDetailResponse] = Field(default_factory=list, description="Lista de work-types asociados con sus pesos de evaluación")
