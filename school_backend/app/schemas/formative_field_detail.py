"""
Schemas para respuesta detallada de campos formativos con work-types.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from decimal import Decimal


class WorkTypeDetail(BaseModel):
    """Schema para work-type con peso de evaluación."""
    work_type_id: int = Field(..., description="ID del tipo de trabajo")
    work_type_name: str = Field(..., description="Nombre del tipo de trabajo")
    evaluation_weight: Decimal = Field(..., description="Peso de evaluación (porcentaje)")
    
    model_config = ConfigDict(from_attributes=True)


class FormativeFieldDetail(BaseModel):
    """Schema para campo formativo con sus work-types."""
    formative_field_id: int = Field(..., description="ID del campo formativo")
    name: str = Field(..., description="Nombre del campo formativo")
    code: Optional[str] = Field(None, description="Código del campo formativo")
    work_types: List[WorkTypeDetail] = Field(default_factory=list, description="Lista de work-types asociados con sus pesos de evaluación")
    
    model_config = ConfigDict(from_attributes=True)


class FormativeFieldsByCycleResponse(BaseModel):
    """Schema de respuesta para campos formativos agrupados por ciclo escolar."""
    school_cycle_id: int = Field(..., description="ID del ciclo escolar")
    formative_fields: List[FormativeFieldDetail] = Field(..., description="Lista de campos formativos con sus work-types")

