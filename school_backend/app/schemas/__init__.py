"""
Módulo de schemas Pydantic.
Exporta todos los schemas de validación de datos.
"""
from app.schemas.catalog import (
    SchoolTypeCreate,
    SchoolTypeResponse,
    ShiftCreate,
    ShiftResponse,
    AccessLevelCreate,
    AccessLevelResponse,
    PeriodCatalogCreate,
    PeriodCatalogResponse
)
from app.schemas.school import (
    SchoolCreate,
    SchoolUpdate,
    SchoolResponse
)
from app.schemas.user import (
    UserCreate,
    UserRegister,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    AccessCodeCreate,
    AccessCodeUpdate,
    AccessCodeResponse
)
from app.schemas.cycle import (
    SchoolCycleCreate,
    SchoolCycleUpdate,
    SchoolCycleResponse
)
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse
)
from app.schemas.partial import (
    PartialCreate,
    PartialCreateList,
    PartialUpdate,
    PartialResponse
)
from app.schemas.learning_field import (
    FormativeFieldCreate,
    FormativeFieldUpdate,
    FormativeFieldResponse
)
from app.schemas.work_type import (
    WorkTypeCreate,
    WorkTypeUpdate,
    WorkTypeResponse
)
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceResponse
)
from app.schemas.student_work import (
    StudentWorkCreate,
    StudentWorkUpdate,
    StudentWorkResponse
)

__all__ = [
    "SchoolTypeCreate",
    "SchoolTypeResponse",
    "ShiftCreate",
    "ShiftResponse",
    "AccessLevelCreate",
    "AccessLevelResponse",
    "PeriodCatalogCreate",
    "PeriodCatalogResponse",
    "SchoolCreate",
    "SchoolUpdate",
    "SchoolResponse",
    "UserCreate",
    "UserRegister",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "AccessCodeCreate",
    "AccessCodeUpdate",
    "AccessCodeResponse",
    "SchoolCycleCreate",
    "SchoolCycleUpdate",
    "SchoolCycleResponse",
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    "PartialCreate",
    "PartialCreateList",
    "PartialUpdate",
    "PartialResponse",
    "FormativeFieldCreate",
    "FormativeFieldUpdate",
    "FormativeFieldResponse",
    "WorkTypeCreate",
    "WorkTypeUpdate",
    "WorkTypeResponse",
    "AttendanceCreate",
    "AttendanceUpdate",
    "AttendanceResponse",
    "StudentWorkCreate",
    "StudentWorkUpdate",
    "StudentWorkResponse",
]

