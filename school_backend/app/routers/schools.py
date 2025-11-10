"""
Router para gestión de escuelas.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.catalog import School, PeriodCatalog
from sqlalchemy.orm import joinedload
from app.models.user import User
from app.schemas.school import SchoolCreate, SchoolUpdate, SchoolResponse
from app.schemas.catalog import PeriodCatalogResponse
from app.schemas.response import GenericResponse, success_response, created_response
from app.dependencies import get_current_active_user, require_access_level
from app.exceptions import NotFoundError, ConflictError

router = APIRouter(
    prefix="/schools",
    tags=["schools"]
)


@router.post("/", response_model=GenericResponse[SchoolResponse], status_code=status.HTTP_201_CREATED)
async def create_school(
    school_data: SchoolCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_access_level("Administrador"))]
):
    """
    Crea una nueva escuela.
    Requiere nivel de acceso: Administrador
    """
    # Verificar si el CCT ya existe
    existing_school = db.query(School).filter(School.cct == school_data.cct).first()
    if existing_school:
        raise ConflictError(f"El CCT {school_data.cct} ya está registrado")
    
    new_school = School(**school_data.model_dump())
    db.add(new_school)
    db.commit()
    db.refresh(new_school)
    
    # Recargar la escuela con la relación shift
    school_with_shift = db.query(School).options(joinedload(School.shift)).filter(School.id == new_school.id).first()
    
    # Obtener todos los periodos del catálogo
    period_catalog_list = db.query(PeriodCatalog).order_by(PeriodCatalog.type_name, PeriodCatalog.period_number).all()
    period_catalog_response = [PeriodCatalogResponse.model_validate(period) for period in period_catalog_list]
    
    # Crear la respuesta de la escuela
    school_dict = {
        "id": school_with_shift.id,
        "cct": school_with_shift.cct,
        "school_type_id": school_with_shift.school_type_id,
        "name": school_with_shift.name,
        "postal_code": school_with_shift.postal_code,
        "latitude": school_with_shift.latitude,
        "longitude": school_with_shift.longitude,
        "shift_id": school_with_shift.shift_id,
        "shift_name": school_with_shift.shift.name if school_with_shift.shift else None,
        "created_at": school_with_shift.created_at,
        "period_catalog": period_catalog_response
    }
    
    school_response = SchoolResponse.model_validate(school_dict)
    return created_response(data=school_response)


@router.get("/", response_model=GenericResponse[List[SchoolResponse]])
async def list_schools(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None, description="Buscar por nombre o CCT")
):
    """
    Lista todas las escuelas con paginación y búsqueda.
    Incluye el catálogo completo de periodos y el nombre del turno.
    """
    query = db.query(School).options(joinedload(School.shift))
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                School.name.like(search_pattern),
                School.cct.like(search_pattern)
            )
        )
    
    schools = query.offset(skip).limit(limit).all()
    
    # Obtener todos los periodos del catálogo (una sola vez para todas las escuelas)
    period_catalog_list = db.query(PeriodCatalog).order_by(PeriodCatalog.type_name, PeriodCatalog.period_number).all()
    period_catalog_response = [PeriodCatalogResponse.model_validate(period) for period in period_catalog_list]
    
    # Construir la lista de escuelas con shift_name y period_catalog
    schools_list = []
    for school in schools:
        school_dict = {
            "id": school.id,
            "cct": school.cct,
            "school_type_id": school.school_type_id,
            "name": school.name,
            "postal_code": school.postal_code,
            "latitude": school.latitude,
            "longitude": school.longitude,
            "shift_id": school.shift_id,
            "shift_name": school.shift.name if school.shift else None,
            "created_at": school.created_at,
            "period_catalog": period_catalog_response
        }
        schools_list.append(SchoolResponse.model_validate(school_dict))
    
    return success_response(data=schools_list)


@router.get("/{cct}", response_model=GenericResponse[SchoolResponse])
async def get_school(
    cct: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene una escuela por CCT (Clave de Centro de Trabajo).
    Incluye el catálogo completo de periodos y el nombre del turno.
    """
    school = db.query(School).options(joinedload(School.shift)).filter(School.cct == cct).first()
    if not school:
        raise NotFoundError("Escuela", cct)
    
    # Obtener todos los periodos del catálogo
    period_catalog_list = db.query(PeriodCatalog).order_by(PeriodCatalog.type_name, PeriodCatalog.period_number).all()
    period_catalog_response = [PeriodCatalogResponse.model_validate(period) for period in period_catalog_list]
    
    # Crear la respuesta de la escuela
    school_dict = {
        "id": school.id,
        "cct": school.cct,
        "school_type_id": school.school_type_id,
        "name": school.name,
        "postal_code": school.postal_code,
        "latitude": school.latitude,
        "longitude": school.longitude,
        "shift_id": school.shift_id,
        "shift_name": school.shift.name if school.shift else None,
        "created_at": school.created_at,
        "period_catalog": period_catalog_response
    }
    
    school_response = SchoolResponse.model_validate(school_dict)
    return success_response(data=school_response)


@router.put("/{cct}", response_model=GenericResponse[SchoolResponse])
async def update_school(
    cct: str,
    school_data: SchoolUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_access_level("Administrador"))]
):
    """
    Actualiza una escuela por CCT (Clave de Centro de Trabajo).
    Requiere nivel de acceso: Administrador
    """
    school = db.query(School).filter(School.cct == cct).first()
    if not school:
        raise NotFoundError("Escuela", cct)
    
    # Verificar CCT si se está actualizando
    update_data = school_data.model_dump(exclude_unset=True)
    if "cct" in update_data and update_data["cct"] != school.cct:
        existing_school = db.query(School).filter(School.cct == update_data["cct"]).first()
        if existing_school:
            raise ConflictError(f"El CCT {update_data['cct']} ya está registrado")
    
    for field, value in update_data.items():
        setattr(school, field, value)
    
    db.commit()
    db.refresh(school)
    
    # Recargar la escuela con la relación shift
    school_with_shift = db.query(School).options(joinedload(School.shift)).filter(School.cct == cct).first()
    
    # Obtener todos los periodos del catálogo
    period_catalog_list = db.query(PeriodCatalog).order_by(PeriodCatalog.type_name, PeriodCatalog.period_number).all()
    period_catalog_response = [PeriodCatalogResponse.model_validate(period) for period in period_catalog_list]
    
    # Crear la respuesta de la escuela
    school_dict = {
        "id": school_with_shift.id,
        "cct": school_with_shift.cct,
        "school_type_id": school_with_shift.school_type_id,
        "name": school_with_shift.name,
        "postal_code": school_with_shift.postal_code,
        "latitude": school_with_shift.latitude,
        "longitude": school_with_shift.longitude,
        "shift_id": school_with_shift.shift_id,
        "shift_name": school_with_shift.shift.name if school_with_shift.shift else None,
        "created_at": school_with_shift.created_at,
        "period_catalog": period_catalog_response
    }
    
    school_response = SchoolResponse.model_validate(school_dict)
    return success_response(data=school_response)


@router.delete("/{cct}", response_model=GenericResponse[str])
async def delete_school(
    cct: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_access_level("Administrador"))]
):
    """
    Elimina una escuela por CCT (Clave de Centro de Trabajo).
    Requiere nivel de acceso: Administrador
    """
    school = db.query(School).filter(School.cct == cct).first()
    if not school:
        raise NotFoundError("Escuela", cct)
    
    db.delete(school)
    db.commit()
    
    return success_response(data="El elemento se ha borrado correctamente")

