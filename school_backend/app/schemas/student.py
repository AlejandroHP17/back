"""
Schemas para estudiantes.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional


class StudentBase(BaseModel):
    """Schema base para estudiante."""
    curp: str = Field(..., min_length=18, max_length=18, description="CURP del estudiante")
    first_name: str = Field(..., min_length=1, max_length=100, description="Nombre")
    last_name: str = Field(..., min_length=1, max_length=100, description="Primer apellido")
    second_last_name: str = Field(..., min_length=1, max_length=100, description="Segundo apellido")
    birth_date: Optional[date] = Field(None, description="Fecha de nacimiento")
    phone: Optional[str] = Field(None, max_length=30, description="Teléfono")
    teacher_id: int = Field(..., description="ID del profesor")
    school_cycle_id: int = Field(..., description="ID del ciclo escolar")
    is_active: bool = Field(True, description="Estado activo/inactivo")


class StudentCreate(StudentBase):
    """Schema para crear un estudiante."""
    pass


class StudentUpdate(BaseModel):
    """Schema para actualizar un estudiante."""
    curp: Optional[str] = Field(None, min_length=18, max_length=18)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    second_last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    birth_date: Optional[date] = None
    phone: Optional[str] = Field(None, max_length=30)
    teacher_id: Optional[int] = None
    school_cycle_id: Optional[int] = None
    is_active: Optional[bool] = None


class StudentResponse(StudentBase):
    """Schema de respuesta para estudiante."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

