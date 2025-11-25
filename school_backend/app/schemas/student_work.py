"""
Schemas para trabajos de estudiantes.
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal


class StudentWorkBase(BaseModel):
    """Schema base para trabajo de estudiante."""
    student_id: int = Field(..., description="ID del estudiante")
    formative_field_id: int = Field(..., description="ID del campo formativo")
    partial_id: int = Field(..., description="ID del parcial")
    work_type_id: int = Field(..., description="ID del tipo de trabajo")
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del trabajo")
    grade: Optional[Decimal] = Field(default=None, description="Calificación (0.0 a 10.0, máximo un decimal)")
    work_date: Optional[date] = Field(default=None, description="Fecha del trabajo")
    
    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v):
        """Valida que la calificación esté entre 0 y 10 con máximo un decimal."""
        if v is not None:
            from decimal import Decimal, ROUND_HALF_UP
            # Asegurar que sea Decimal
            if isinstance(v, (int, float, str)):
                v = Decimal(str(v))
            elif not isinstance(v, Decimal):
                return v
            
            if v < 0 or v > 10:
                raise ValueError("La calificación debe estar entre 0 y 10")
            
            # Redondear a máximo un decimal y verificar
            rounded = v.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            # Convertir a string para verificar decimales significativos
            str_grade = str(rounded)
            if '.' in str_grade:
                decimal_part = str_grade.split('.')[1]
                # Contar solo dígitos significativos (sin ceros al final)
                significant_decimals = len(decimal_part.rstrip('0'))
                if significant_decimals > 1:
                    raise ValueError("La calificación solo puede tener máximo un decimal (ejemplo: 7.5)")
            return rounded
        return v


class StudentWorkCreate(StudentWorkBase):
    """Schema para crear un trabajo de estudiante."""
    pass


class StudentWorkUpdate(BaseModel):
    """Schema para actualizar un trabajo de estudiante."""
    student_id: Optional[int] = None
    formative_field_id: Optional[int] = None
    partial_id: Optional[int] = None
    work_type_id: Optional[int] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    grade: Optional[Decimal] = Field(default=None)
    work_date: Optional[date] = None
    
    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v):
        """Valida que la calificación esté entre 0 y 10 con máximo un decimal."""
        if v is not None:
            from decimal import Decimal, ROUND_HALF_UP
            # Asegurar que sea Decimal
            if isinstance(v, (int, float, str)):
                v = Decimal(str(v))
            elif not isinstance(v, Decimal):
                return v
            
            if v < 0 or v > 10:
                raise ValueError("La calificación debe estar entre 0 y 10")
            
            # Redondear a máximo un decimal y verificar
            rounded = v.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            # Convertir a string para verificar decimales significativos
            str_grade = str(rounded)
            if '.' in str_grade:
                decimal_part = str_grade.split('.')[1]
                # Contar solo dígitos significativos (sin ceros al final)
                significant_decimals = len(decimal_part.rstrip('0'))
                if significant_decimals > 1:
                    raise ValueError("La calificación solo puede tener máximo un decimal (ejemplo: 7.5)")
            return rounded
        return v


class StudentWorkResponse(StudentWorkBase):
    """Schema de respuesta para trabajo de estudiante."""
    id: int
    teacher_id: int
    created_at: datetime
    student_name: Optional[str] = Field(None, description="Nombre completo del estudiante")
    formative_field_name: Optional[str] = Field(None, description="Nombre del campo formativo")
    partial_name: Optional[str] = Field(None, description="Nombre del parcial")
    work_type_name: Optional[str] = Field(None, description="Nombre del tipo de trabajo")
    school_cycle_name: Optional[str] = Field(None, description="Nombre del ciclo escolar")
    school_name: Optional[str] = Field(None, description="Nombre de la escuela")
    
    @field_validator('grade', mode='before')
    @classmethod
    def normalize_grade_from_db(cls, v):
        """Normaliza la calificación cuando viene de la base de datos (ej: Decimal('10.00') -> Decimal('10.0'))."""
        if v is not None:
            from decimal import Decimal, ROUND_HALF_UP
            # Asegurar que sea Decimal
            if isinstance(v, (int, float, str)):
                v = Decimal(str(v))
            elif not isinstance(v, Decimal):
                return v
            # Redondear a máximo un decimal significativo
            # Usamos quantize para redondear a 1 decimal
            normalized = v.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            return normalized
        return v
    
    model_config = ConfigDict(from_attributes=True)


class StudentWorkCreateResponse(StudentWorkBase):
    """Schema de respuesta para creación de trabajo de estudiante (sin school_name ni school_cycle_name)."""
    id: int
    teacher_id: int
    created_at: datetime
    student_name: Optional[str] = Field(None, description="Nombre completo del estudiante")
    formative_field_name: Optional[str] = Field(None, description="Nombre del campo formativo")
    partial_name: Optional[str] = Field(None, description="Nombre del parcial")
    work_type_name: Optional[str] = Field(None, description="Nombre del tipo de trabajo")
    
    @field_validator('grade', mode='before')
    @classmethod
    def normalize_grade_from_db(cls, v):
        """Normaliza la calificación cuando viene de la base de datos (ej: Decimal('10.00') -> Decimal('10.0'))."""
        if v is not None:
            from decimal import Decimal, ROUND_HALF_UP
            # Asegurar que sea Decimal
            if isinstance(v, (int, float, str)):
                v = Decimal(str(v))
            elif not isinstance(v, Decimal):
                return v
            # Redondear a máximo un decimal significativo
            # Usamos quantize para redondear a 1 decimal
            normalized = v.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            return normalized
        return v
    
    model_config = ConfigDict(from_attributes=True)


class StudentWorkGradeItem(BaseModel):
    """Schema para un elemento de calificación en el bulk."""
    student_id: int = Field(..., description="ID del estudiante")
    grade: Optional[Decimal] = Field(default=None, description="Calificación (0.0 a 10.0, máximo un decimal). Si no se proporciona, será null.")
    
    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v):
        """Valida que la calificación esté entre 0 y 10 con máximo un decimal."""
        if v is not None:
            from decimal import Decimal, ROUND_HALF_UP
            # Asegurar que sea Decimal
            if isinstance(v, (int, float, str)):
                v = Decimal(str(v))
            elif not isinstance(v, Decimal):
                return v
            
            if v < 0 or v > 10:
                raise ValueError("La calificación debe estar entre 0 y 10")
            
            # Redondear a máximo un decimal y verificar
            rounded = v.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            # Convertir a string para verificar decimales significativos
            str_grade = str(rounded)
            if '.' in str_grade:
                decimal_part = str_grade.split('.')[1]
                # Contar solo dígitos significativos (sin ceros al final)
                significant_decimals = len(decimal_part.rstrip('0'))
                if significant_decimals > 1:
                    raise ValueError("La calificación solo puede tener máximo un decimal (ejemplo: 7.5)")
            return rounded
        return v


class StudentWorkBulkCreate(BaseModel):
    """Schema para crear trabajos de estudiantes en masa."""
    formative_field_id: int = Field(..., description="ID del campo formativo")
    partial_id: int = Field(..., description="ID del parcial")
    work_type_id: int = Field(..., description="ID del tipo de trabajo")
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del trabajo")
    work_date: Optional[date] = Field(default=None, description="Fecha del trabajo")
    grades: List[StudentWorkGradeItem] = Field(..., description="Lista de calificaciones por estudiante")
    school_cycle_id: Optional[int] = Field(None, description="ID del ciclo escolar (opcional, valida que estudiantes pertenezcan al ciclo)")


class StudentWorkBulkResponse(BaseModel):
    """Schema de respuesta para creación masiva de trabajos."""
    created: List[StudentWorkCreateResponse] = Field(..., description="Trabajos creados")
    total_with_grade: int = Field(..., description="Total de estudiantes con calificación")
    total_without_grade: int = Field(..., description="Total de estudiantes sin calificación (null)")
    formative_field_name: Optional[str] = Field(None, description="Nombre del campo formativo usado")
    partial_name: Optional[str] = Field(None, description="Nombre del parcial usado")
    work_type_id: int = Field(..., description="ID del tipo de trabajo usado")
    work_type_name: Optional[str] = Field(None, description="Nombre del tipo de trabajo usado")
    name: str = Field(..., description="Nombre del trabajo")

