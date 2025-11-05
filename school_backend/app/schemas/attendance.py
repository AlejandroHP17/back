"""
Schemas para asistencias.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, Literal


class AttendanceBase(BaseModel):
    """Schema base para asistencia."""
    student_id: int = Field(..., description="ID del estudiante")
    partial_id: int = Field(..., description="ID del parcial")
    school_cycle_id: int = Field(..., description="ID del ciclo escolar")
    attendance_date: date = Field(..., description="Fecha de asistencia")
    status: Literal['present', 'absent', 'late'] = Field(default='present', description="Estado de asistencia: present, absent, late")


class AttendanceCreate(AttendanceBase):
    """Schema para crear una asistencia."""
    pass


class AttendanceUpdate(BaseModel):
    """Schema para actualizar una asistencia."""
    student_id: Optional[int] = None
    partial_id: Optional[int] = None
    school_cycle_id: Optional[int] = None
    attendance_date: Optional[date] = None
    status: Optional[Literal['present', 'absent', 'late']] = None


class AttendanceResponse(AttendanceBase):
    """Schema de respuesta para asistencia."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

