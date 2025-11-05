"""
Schemas para pesos de evaluación de tipos de trabajo.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal


class WorkTypeEvaluationBase(BaseModel):
    """Schema base para peso de evaluación."""
    formative_field_id: int = Field(..., description="ID del campo formativo")
    partial_id: int = Field(..., description="ID del parcial")
    work_type_id: int = Field(..., description="ID del tipo de trabajo")
    evaluation_weight: Decimal = Field(..., ge=0, le=100, description="Peso de evaluación (porcentaje, ej: 20.00)")


class WorkTypeEvaluationCreate(WorkTypeEvaluationBase):
    """Schema para crear un peso de evaluación."""
    pass


class WorkTypeEvaluationUpdate(BaseModel):
    """Schema para actualizar un peso de evaluación."""
    formative_field_id: Optional[int] = None
    partial_id: Optional[int] = None
    work_type_id: Optional[int] = None
    evaluation_weight: Optional[Decimal] = Field(None, ge=0, le=100)


class WorkTypeEvaluationResponse(WorkTypeEvaluationBase):
    """Schema de respuesta para peso de evaluación."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

