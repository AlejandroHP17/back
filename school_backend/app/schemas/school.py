"""
Schemas para escuelas.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal


class SchoolBase(BaseModel):
    """Schema base para escuela."""
    cct: str = Field(..., min_length=1, max_length=50, description="Clave de Centro de Trabajo")
    school_type_id: int = Field(..., description="ID del tipo de escuela")
    name: str = Field(..., min_length=1, max_length=255, description="Nombre de la escuela")
    postal_code: Optional[str] = Field(None, max_length=10, description="Código postal")
    latitude: Optional[Decimal] = Field(None, description="Latitud")
    longitude: Optional[Decimal] = Field(None, description="Longitud")
    shift_id: Optional[int] = Field(None, description="ID del turno")
    period_catalog_id: Optional[int] = Field(None, description="ID del catálogo de periodo")


class SchoolCreate(SchoolBase):
    """Schema para crear una escuela."""
    pass


class SchoolUpdate(BaseModel):
    """Schema para actualizar una escuela."""
    cct: Optional[str] = Field(None, min_length=1, max_length=50)
    school_type_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=10)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    shift_id: Optional[int] = None
    period_catalog_id: Optional[int] = None


class SchoolResponse(SchoolBase):
    """Schema de respuesta para escuela."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

