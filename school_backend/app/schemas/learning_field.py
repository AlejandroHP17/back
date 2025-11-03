"""
Schemas para campos formativos.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class FormativeFieldBase(BaseModel):
    """Schema base para campo formativo."""
    school_cycle_id: int = Field(..., description="ID del ciclo escolar")
    name: str = Field(..., min_length=1, max_length=120, description="Nombre del campo formativo")
    code: Optional[str] = Field(None, max_length=50, description="Código del campo formativo")


class FormativeFieldCreate(FormativeFieldBase):
    """Schema para crear un campo formativo."""
    pass


class FormativeFieldUpdate(BaseModel):
    """Schema para actualizar un campo formativo."""
    school_cycle_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    code: Optional[str] = Field(None, max_length=50)


class FormativeFieldResponse(FormativeFieldBase):
    """Schema de respuesta para campo formativo."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

