"""
Schema para crear campo formativo con work-types y evaluaciones en una sola operación.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from decimal import Decimal


class WorkTypeItem(BaseModel):
    """Item de work-type que puede ser nuevo o existente."""
    id: Optional[int] = Field(None, description="ID del work-type existente (si se proporciona, se usa el existente)")
    name: Optional[str] = Field(None, min_length=1, max_length=120, description="Nombre del work-type (requerido si id es None para crear uno nuevo)")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v, info):
        """Valida que si no hay ID, debe haber nombre."""
        if info.data.get('id') is None and (v is None or v == ""):
            raise ValueError("El nombre es requerido cuando no se proporciona un ID (work-type nuevo)")
        return v


class WorkTypeEvaluationItem(BaseModel):
    """Item de evaluación con porcentaje para un work-type (nuevo o existente)."""
    partial_id: int = Field(..., description="ID del parcial")
    work_type_id: Optional[int] = Field(None, description="ID del work-type existente (si es null, se busca por work_type_name)")
    work_type_name: Optional[str] = Field(None, min_length=1, max_length=120, description="Nombre del work-type (requerido si work_type_id es null)")
    evaluation_weight: Decimal = Field(..., ge=0, le=100, description="Peso de evaluación (porcentaje, ej: 20.00)")
    
    @field_validator('work_type_name')
    @classmethod
    def validate_work_type_name(cls, v, info):
        """Valida que si work_type_id es null, debe haber work_type_name."""
        if info.data.get('work_type_id') is None and (v is None or v == ""):
            raise ValueError("work_type_name es requerido cuando work_type_id es null")
        return v


class FormativeFieldBulkCreate(BaseModel):
    """Schema para crear campo formativo con work-types y evaluaciones en una sola operación."""
    school_cycle_id: int = Field(..., description="ID del ciclo escolar")
    name: str = Field(..., min_length=1, max_length=120, description="Nombre del campo formativo (ej: Español, Matemáticas)")
    code: Optional[str] = Field(None, max_length=50, description="Código del campo formativo")
    work_types: List[WorkTypeItem] = Field(..., description="Lista de work-types (pueden ser nuevos o existentes por ID)")
    evaluations: List[WorkTypeEvaluationItem] = Field(..., description="Lista de evaluaciones con porcentajes (para work-types nuevos o existentes)")

