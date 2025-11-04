"""
Schemas para parciales.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, List


class PartialBase(BaseModel):
    """Schema base para parcial."""
    school_cycle_id: int = Field(..., description="ID del ciclo escolar")
    name: str = Field(..., min_length=1, max_length=80, description="Nombre del parcial")
    start_date: Optional[date] = Field(None, description="Fecha de inicio")
    end_date: Optional[date] = Field(None, description="Fecha de fin")


class PartialCreate(PartialBase):
    """Schema para crear un parcial."""
    pass


class PartialCreateList(BaseModel):
    """Schema para crear múltiples parciales."""
    partials: List[PartialCreate] = Field(..., min_items=1, description="Lista de parciales a crear")


class PartialUpdate(BaseModel):
    """Schema para actualizar un parcial."""
    school_cycle_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PartialResponse(PartialBase):
    """Schema de respuesta para parcial."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

