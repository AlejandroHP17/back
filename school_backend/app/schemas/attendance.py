"""
Schemas para asistencias.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, Literal, List


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
    student_name: Optional[str] = Field(None, description="Nombre completo del estudiante")
    partial_name: Optional[str] = Field(None, description="Nombre del parcial")
    school_cycle_name: Optional[str] = Field(None, description="Nombre del ciclo escolar")
    school_name: Optional[str] = Field(None, description="Nombre de la escuela")
    
    model_config = ConfigDict(from_attributes=True)


class AttendanceCreateResponse(AttendanceBase):
    """Schema de respuesta para creación de asistencia (sin school_name ni school_cycle_name)."""
    id: int
    created_at: datetime
    student_name: Optional[str] = Field(None, description="Nombre completo del estudiante")
    partial_name: Optional[str] = Field(None, description="Nombre del parcial")
    
    model_config = ConfigDict(from_attributes=True)


class AttendanceBulkCreate(BaseModel):
    """Schema para crear asistencias en masa."""
    student_ids: List[int] = Field(..., description="Lista de IDs de estudiantes presentes")
    attendance_date: date = Field(..., description="Fecha de asistencia")
    school_cycle_id: Optional[int] = Field(None, description="ID del ciclo escolar (opcional, usa el activo si no se especifica)")
    partial_id: Optional[int] = Field(None, description="ID del parcial (opcional, usa el activo si no se especifica)")


class AttendanceBulkResponse(BaseModel):
    """Schema de respuesta para creación masiva de asistencias."""
    created: List[AttendanceCreateResponse] = Field(..., description="Asistencias creadas")
    updated: List[AttendanceCreateResponse] = Field(..., description="Asistencias actualizadas (si ya existían)")
    total_present: int = Field(..., description="Total de estudiantes presentes")
    total_absent: int = Field(..., description="Total de estudiantes ausentes")
    school_cycle_id: int = Field(..., description="ID del ciclo escolar usado")
    partial_id: int = Field(..., description="ID del parcial usado")
    attendance_date: date = Field(..., description="Fecha de asistencia")

