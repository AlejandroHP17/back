"""
Schemas para tipos de trabajo.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal


class WorkTypeBase(BaseModel):
    """Schema base para tipo de trabajo."""
    teacher_id: int = Field(..., description="ID del profesor")
    learning_field_id: Optional[int] = Field(None, description="ID del campo formativo")
    name: str = Field(..., min_length=1, max_length=150, description="Nombre del tipo de trabajo")
    percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Porcentaje del tipo de trabajo")
    is_active: bool = Field(True, description="Estado activo/inactivo")


class WorkTypeCreate(WorkTypeBase):
    """Schema para crear un tipo de trabajo."""
    pass


class WorkTypeUpdate(BaseModel):
    """Schema para actualizar un tipo de trabajo."""
    teacher_id: Optional[int] = None
    learning_field_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class WorkTypeResponse(WorkTypeBase):
    """Schema de respuesta para tipo de trabajo."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

