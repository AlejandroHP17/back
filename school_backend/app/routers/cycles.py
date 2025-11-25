"""
Router para gestión de ciclos escolares.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.database import get_db
from app.models.cycle import SchoolCycle
from app.models.user import User
from app.models.catalog import School
from app.schemas.cycle import SchoolCycleCreate, SchoolCycleUpdate, SchoolCycleResponse, SchoolCycleCreateResponse
from app.schemas.response import GenericResponse, success_response, created_response
from app.dependencies import get_current_active_user
from app.exceptions import NotFoundError

router = APIRouter(
    prefix="/cycles",
    tags=["school-cycles"]
)


@router.post("/", response_model=GenericResponse[SchoolCycleCreateResponse], status_code=status.HTTP_201_CREATED)
async def create_cycle(
    cycle_data: SchoolCycleCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Crea un nuevo ciclo escolar.
    """
    # Excluir is_active para usar el default de la BD
    cycle_dict = cycle_data.model_dump(exclude={"is_active"})
    new_cycle = SchoolCycle(**cycle_dict)
    db.add(new_cycle)
    db.commit()
    db.refresh(new_cycle)
    
    # Cargar relaciones para obtener nombres
    cycle = db.query(SchoolCycle).options(
        joinedload(SchoolCycle.teacher)
    ).filter(SchoolCycle.id == new_cycle.id).first()
    
    cycle_dict = {
        "id": cycle.id,
        "teacher_id": cycle.teacher_id,
        "school_id": cycle.school_id,
        "name": cycle.name,
        "cycle_label": cycle.cycle_label,
        "grade": cycle.grade,
        "group_name": cycle.group_name,
        "period_catalog_id": cycle.period_catalog_id,
        "is_active": cycle.is_active,
        "created_at": cycle.created_at,
        "teacher_name": cycle.teacher.full_name if cycle.teacher else None
    }
    cycle_response = SchoolCycleCreateResponse.model_validate(cycle_dict)
    return created_response(data=cycle_response)


@router.get("/", response_model=GenericResponse[List[SchoolCycleResponse]])
async def list_cycles(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    teacher_id: int = Query(None, description="Filtrar por ID de profesor"),
    school_id: int = Query(None, description="Filtrar por ID de escuela"),
    is_active: bool = Query(None, description="Filtrar por estado activo")
):
    """
    Lista todos los ciclos escolares con filtros y paginación.
    """
    query = db.query(SchoolCycle)
    
    if teacher_id:
        query = query.filter(SchoolCycle.teacher_id == teacher_id)
    
    if school_id:
        query = query.filter(SchoolCycle.school_id == school_id)
    
    if is_active is not None:
        query = query.filter(SchoolCycle.is_active == is_active)
    
    # Cargar relaciones necesarias
    cycles = query.options(
        joinedload(SchoolCycle.school),
        joinedload(SchoolCycle.teacher)
    ).offset(skip).limit(limit).all()
    
    # Construir respuestas con nombres
    cycles_list = []
    for cycle in cycles:
        cycle_dict = {
            "id": cycle.id,
            "teacher_id": cycle.teacher_id,
            "school_id": cycle.school_id,
            "name": cycle.name,
            "cycle_label": cycle.cycle_label,
            "grade": cycle.grade,
            "group_name": cycle.group_name,
            "period_catalog_id": cycle.period_catalog_id,
            "is_active": cycle.is_active,
            "created_at": cycle.created_at,
            "school_name": cycle.school.name if cycle.school else None,
            "teacher_name": cycle.teacher.full_name if cycle.teacher else None
        }
        cycles_list.append(SchoolCycleResponse.model_validate(cycle_dict))
    
    return success_response(data=cycles_list)


@router.get("/{cycle_id}", response_model=GenericResponse[SchoolCycleResponse])
async def get_cycle(
    cycle_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene un ciclo escolar por ID.
    """
    cycle = db.query(SchoolCycle).options(
        joinedload(SchoolCycle.school),
        joinedload(SchoolCycle.teacher)
    ).filter(SchoolCycle.id == cycle_id).first()
    if not cycle:
        raise NotFoundError("Ciclo escolar", str(cycle_id))
    
    cycle_dict = {
        "id": cycle.id,
        "teacher_id": cycle.teacher_id,
        "school_id": cycle.school_id,
        "name": cycle.name,
        "cycle_label": cycle.cycle_label,
        "grade": cycle.grade,
        "group_name": cycle.group_name,
        "period_catalog_id": cycle.period_catalog_id,
        "is_active": cycle.is_active,
        "created_at": cycle.created_at,
        "school_name": cycle.school.name if cycle.school else None,
        "teacher_name": cycle.teacher.full_name if cycle.teacher else None
    }
    cycle_response = SchoolCycleResponse.model_validate(cycle_dict)
    return success_response(data=cycle_response)


@router.put("/{cycle_id}", response_model=GenericResponse[SchoolCycleResponse])
async def update_cycle(
    cycle_id: int,
    cycle_data: SchoolCycleUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Actualiza un ciclo escolar.
    """
    cycle = db.query(SchoolCycle).filter(SchoolCycle.id == cycle_id).first()
    if not cycle:
        raise NotFoundError("Ciclo escolar", str(cycle_id))
    
    update_data = cycle_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cycle, field, value)
    
    db.commit()
    db.refresh(cycle)
    
    # Recargar con relaciones
    cycle = db.query(SchoolCycle).options(
        joinedload(SchoolCycle.school),
        joinedload(SchoolCycle.teacher)
    ).filter(SchoolCycle.id == cycle_id).first()
    
    cycle_dict = {
        "id": cycle.id,
        "teacher_id": cycle.teacher_id,
        "school_id": cycle.school_id,
        "name": cycle.name,
        "cycle_label": cycle.cycle_label,
        "grade": cycle.grade,
        "group_name": cycle.group_name,
        "period_catalog_id": cycle.period_catalog_id,
        "is_active": cycle.is_active,
        "created_at": cycle.created_at,
        "school_name": cycle.school.name if cycle.school else None,
        "teacher_name": cycle.teacher.full_name if cycle.teacher else None
    }
    cycle_response = SchoolCycleResponse.model_validate(cycle_dict)
    return success_response(data=cycle_response)


@router.delete("/{cycle_id}", response_model=GenericResponse[str])
async def delete_cycle(
    cycle_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Elimina un ciclo escolar.
    """
    cycle = db.query(SchoolCycle).filter(SchoolCycle.id == cycle_id).first()
    if not cycle:
        raise NotFoundError("Ciclo escolar", str(cycle_id))
    
    db.delete(cycle)
    db.commit()
    
    return success_response(data="El elemento se ha borrado correctamente")

