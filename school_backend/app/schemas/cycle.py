"""
Schemas para ciclos escolares.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class SchoolCycleBase(BaseModel):
    """Schema base para ciclo escolar."""
    teacher_id: int = Field(..., description="ID del profesor")
    school_id: int = Field(..., description="ID de la escuela")
    name: str = Field(..., min_length=1, max_length=150, description="Nombre del ciclo")
    description: Optional[str] = Field(None, description="Descripción del ciclo")
    year: int = Field(..., ge=2000, le=3000, description="Año del ciclo")
    turn_id: Optional[int] = Field(None, description="ID del turno")
    grade: Optional[str] = Field(None, max_length=20, description="Grado")
    group_name: Optional[str] = Field(None, max_length=20, description="Grupo")
    is_active: bool = Field(True, description="Estado activo/inactivo")


class SchoolCycleCreate(SchoolCycleBase):
    """Schema para crear un ciclo escolar."""
    pass


class SchoolCycleUpdate(BaseModel):
    """Schema para actualizar un ciclo escolar."""
    teacher_id: Optional[int] = None
    school_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    year: Optional[int] = Field(None, ge=2000, le=3000)
    turn_id: Optional[int] = None
    grade: Optional[str] = Field(None, max_length=20)
    group_name: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class SchoolCycleResponse(SchoolCycleBase):
    """Schema de respuesta para ciclo escolar."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

