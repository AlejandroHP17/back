"""
Schemas para trabajos de estudiantes.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional
from decimal import Decimal


class StudentWorkBase(BaseModel):
    """Schema base para trabajo de estudiante."""
    student_id: int = Field(..., description="ID del estudiante")
    partial_id: int = Field(..., description="ID del parcial")
    learning_field_id: int = Field(..., description="ID del campo formativo")
    work_type_id: Optional[int] = Field(default=None, description="ID del tipo de trabajo")
    teacher_id: int = Field(..., description="ID del profesor")
    name: str = Field(..., min_length=1, max_length=255, description="Nombre del trabajo")
    grade: Optional[Decimal] = Field(default=None, ge=0, description="Calificación")
    work_date: Optional[date] = Field(default=None, alias="date", description="Fecha del trabajo")
    
    class Config:
        populate_by_name = True


class StudentWorkCreate(StudentWorkBase):
    """Schema para crear un trabajo de estudiante."""
    pass


class StudentWorkUpdate(BaseModel):
    """Schema para actualizar un trabajo de estudiante."""
    student_id: Optional[int] = None
    partial_id: Optional[int] = None
    learning_field_id: Optional[int] = None
    work_type_id: Optional[int] = None
    teacher_id: Optional[int] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    grade: Optional[Decimal] = Field(default=None, ge=0)
    work_date: Optional[date] = Field(default=None, alias="date")
    
    class Config:
        populate_by_name = True


class StudentWorkResponse(StudentWorkBase):
    """Schema de respuesta para trabajo de estudiante."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

