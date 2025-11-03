"""
Schemas para catálogos (school_types, shifts, access_levels).
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class SchoolTypeBase(BaseModel):
    """Schema base para tipo de escuela."""
    name: str = Field(..., min_length=1, max_length=50, description="Nombre del tipo de escuela")


class SchoolTypeCreate(SchoolTypeBase):
    """Schema para crear un tipo de escuela."""
    pass


class SchoolTypeResponse(SchoolTypeBase):
    """Schema de respuesta para tipo de escuela."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ShiftBase(BaseModel):
    """Schema base para turno."""
    name: str = Field(..., min_length=1, max_length=50, description="Nombre del turno")


class ShiftCreate(ShiftBase):
    """Schema para crear un turno."""
    pass


class ShiftResponse(ShiftBase):
    """Schema de respuesta para turno."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AccessLevelBase(BaseModel):
    """Schema base para nivel de acceso."""
    name: str = Field(..., min_length=1, max_length=50, description="Nombre del nivel de acceso")


class AccessLevelCreate(AccessLevelBase):
    """Schema para crear un nivel de acceso."""
    pass


class AccessLevelResponse(AccessLevelBase):
    """Schema de respuesta para nivel de acceso."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PeriodCatalogBase(BaseModel):
    """Schema base para catálogo de periodos."""
    type_name: str = Field(..., min_length=1, max_length=20, description="Tipo de periodo (ej: Anual, Semestre, Trimestre)")
    period_number: int = Field(..., ge=1, description="Número del periodo (ej: 1, 2, 3)")


class PeriodCatalogCreate(PeriodCatalogBase):
    """Schema para crear un catálogo de periodo."""
    pass


class PeriodCatalogResponse(PeriodCatalogBase):
    """Schema de respuesta para catálogo de periodo."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

