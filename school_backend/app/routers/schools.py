"""
Router para gestión de escuelas.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.catalog import School
from app.models.user import User
from app.schemas.school import SchoolCreate, SchoolUpdate, SchoolResponse
from app.dependencies import get_current_active_user, require_access_level
from app.exceptions import NotFoundError, ConflictError

router = APIRouter(
    prefix="/schools",
    tags=["escuelas"]
)


@router.post("/", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
async def create_school(
    school_data: SchoolCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_access_level("admin", "super_admin"))]
):
    """
    Crea una nueva escuela.
    Requiere nivel de acceso: admin o super_admin
    """
    # Verificar si el CCT ya existe
    existing_school = db.query(School).filter(School.cct == school_data.cct).first()
    if existing_school:
        raise ConflictError(f"El CCT {school_data.cct} ya está registrado")
    
    new_school = School(**school_data.model_dump())
    db.add(new_school)
    db.commit()
    db.refresh(new_school)
    
    return SchoolResponse.model_validate(new_school)


@router.get("/", response_model=List[SchoolResponse])
async def list_schools(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None, description="Buscar por nombre o CCT")
):
    """
    Lista todas las escuelas con paginación y búsqueda.
    """
    query = db.query(School)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                School.name.like(search_pattern),
                School.cct.like(search_pattern)
            )
        )
    
    schools = query.offset(skip).limit(limit).all()
    return [SchoolResponse.model_validate(school) for school in schools]


@router.get("/{school_id}", response_model=SchoolResponse)
async def get_school(
    school_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene una escuela por ID.
    """
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundError("Escuela", str(school_id))
    
    return SchoolResponse.model_validate(school)


@router.put("/{school_id}", response_model=SchoolResponse)
async def update_school(
    school_id: int,
    school_data: SchoolUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_access_level("admin", "super_admin"))]
):
    """
    Actualiza una escuela.
    Requiere nivel de acceso: admin o super_admin
    """
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundError("Escuela", str(school_id))
    
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
    
    return SchoolResponse.model_validate(school)


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school(
    school_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_access_level("super_admin"))]
):
    """
    Elimina una escuela.
    Requiere nivel de acceso: super_admin
    """
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundError("Escuela", str(school_id))
    
    db.delete(school)
    db.commit()
    
    return None

