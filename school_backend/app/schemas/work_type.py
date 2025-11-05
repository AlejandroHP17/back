"""
Schemas para tipos de trabajo.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class WorkTypeBase(BaseModel):
    """Schema base para tipo de trabajo."""
    teacher_id: int = Field(..., description="ID del profesor")
    name: str = Field(..., min_length=1, max_length=120, description="Nombre del tipo de trabajo")


class WorkTypeCreate(WorkTypeBase):
    """Schema para crear un tipo de trabajo."""
    pass


class WorkTypeUpdate(BaseModel):
    """Schema para actualizar un tipo de trabajo."""
    teacher_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=120)


class WorkTypeResponse(WorkTypeBase):
    """Schema de respuesta para tipo de trabajo."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

