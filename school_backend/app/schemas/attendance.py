"""
Schemas para asistencias.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional


class AttendanceBase(BaseModel):
    """Schema base para asistencia."""
    student_id: int = Field(..., description="ID del estudiante")
    partial_id: int = Field(..., description="ID del parcial")
    attended: bool = Field(default=True, description="Estado de asistencia")
    attendance_date: date = Field(..., alias="date", description="Fecha de asistencia")
    notes: Optional[str] = Field(default=None, max_length=255, description="Notas adicionales")
    
    class Config:
        populate_by_name = True


class AttendanceCreate(AttendanceBase):
    """Schema para crear una asistencia."""
    pass


class AttendanceUpdate(BaseModel):
    """Schema para actualizar una asistencia."""
    student_id: Optional[int] = None
    partial_id: Optional[int] = None
    attended: Optional[bool] = None
    attendance_date: Optional[date] = Field(None, alias="date")
    notes: Optional[str] = Field(default=None, max_length=255)
    
    class Config:
        populate_by_name = True


class AttendanceResponse(BaseModel):
    """Schema de respuesta para asistencia."""
    id: int
    student_id: int
    partial_id: int
    attended: bool
    date: date
    notes: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

