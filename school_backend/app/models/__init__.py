"""
Módulo de modelos SQLAlchemy.
Exporta todos los modelos de la base de datos.
"""
from app.models.base import Base
from app.models.catalog import (
    SchoolType,
    Shift,
    AccessLevel,
    PeriodCatalog
)
from app.models.catalog import School
from app.models.user import User, AccessCode
from app.models.cycle import SchoolCycle
from app.models.student import Student
from app.models.partial import Partial
from app.models.formative_field import FormativeField
from app.models.work_type import WorkType
from app.models.work_type_evaluation import WorkTypeEvaluation
from app.models.attendance import Attendance
from app.models.student_work import StudentWork

__all__ = [
    "Base",
    "SchoolType",
    "Shift",
    "AccessLevel",
    "PeriodCatalog",
    "School",
    "User",
    "AccessCode",
    "SchoolCycle",
    "Student",
    "Partial",
    "FormativeField",
    "WorkType",
    "WorkTypeEvaluation",
    "Attendance",
    "StudentWork",
]

