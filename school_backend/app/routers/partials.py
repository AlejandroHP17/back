"""
Router para gestión de parciales.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.partial import Partial
from app.models.cycle import SchoolCycle
from app.models.user import User
from app.schemas.partial import PartialCreate, PartialCreateList, PartialUpdate, PartialResponse
from app.schemas.response import GenericResponse, success_response, created_response
from app.dependencies import get_current_active_user
from app.exceptions import NotFoundError, ConflictError

router = APIRouter(
    prefix="/partials",
    tags=["partials"]
)


@router.post("/", response_model=GenericResponse[List[PartialResponse]], status_code=status.HTTP_201_CREATED)
async def create_partials(
    partials_data: PartialCreateList,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Crea uno o múltiples parciales.
    Solo el profesor dueño del ciclo escolar puede crear parciales.
    Puede recibir una lista de parciales para crear varios a la vez.
    """
    created_partials = []
    
    # Validar todos los parciales antes de crear ninguno
    school_cycle_ids = set()
    for partial_data in partials_data.partials:
        school_cycle_ids.add(partial_data.school_cycle_id)
    
    # Verificar que todos los ciclos existen y pertenecen al profesor
    school_cycles = db.query(SchoolCycle).filter(
        SchoolCycle.id.in_(school_cycle_ids)
    ).all()
    
    if len(school_cycles) != len(school_cycle_ids):
        found_ids = {cycle.id for cycle in school_cycles}
        missing_ids = school_cycle_ids - found_ids
        raise NotFoundError("Ciclo escolar", ", ".join(str(id) for id in missing_ids))
    
    # Verificar que todos los ciclos pertenecen al profesor actual
    for school_cycle in school_cycles:
        if school_cycle.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso para crear parciales en el ciclo escolar {school_cycle.id}. Solo el profesor dueño del ciclo puede crear parciales."
            )
    
    # Crear todos los parciales
    for partial_data in partials_data.partials:
        new_partial = Partial(
            school_cycle_id=partial_data.school_cycle_id,
            name=partial_data.name,
            start_date=partial_data.start_date,
            end_date=partial_data.end_date
        )
        db.add(new_partial)
        created_partials.append(new_partial)
    
    db.commit()
    
    # Refrescar todos los parciales creados
    for partial in created_partials:
        db.refresh(partial)
    
    partials_list = [PartialResponse.model_validate(partial) for partial in created_partials]
    return created_response(data=partials_list)


@router.get("/", response_model=GenericResponse[List[PartialResponse]])
async def list_partials(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    school_cycle_id: int = Query(None, description="Filtrar por ID de ciclo escolar"),
    teacher_id: int = Query(None, description="Filtrar por ID de profesor (solo ciclos del profesor)")
):
    """
    Lista todos los parciales con filtros y paginación.
    Si se especifica teacher_id, solo muestra parciales de ciclos pertenecientes a ese profesor.
    """
    query = db.query(Partial)
    
    # Si se especifica teacher_id, filtrar por ciclos del profesor
    if teacher_id:
        query = query.join(SchoolCycle).filter(SchoolCycle.teacher_id == teacher_id)
    
    # Si se especifica school_cycle_id, filtrar por ciclo
    if school_cycle_id:
        query = query.filter(Partial.school_cycle_id == school_cycle_id)
    
    partials = query.offset(skip).limit(limit).all()
    partials_list = [PartialResponse.model_validate(partial) for partial in partials]
    return success_response(data=partials_list)


@router.get("/{partial_id}", response_model=GenericResponse[PartialResponse])
async def get_partial(
    partial_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene un parcial por ID.
    """
    partial = db.query(Partial).filter(Partial.id == partial_id).first()
    
    if not partial:
        raise NotFoundError("Parcial", str(partial_id))
    
    partial_response = PartialResponse.model_validate(partial)
    return success_response(data=partial_response)


@router.put("/{partial_id}", response_model=GenericResponse[PartialResponse])
async def update_partial(
    partial_id: int,
    partial_data: PartialUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Actualiza un parcial.
    Solo el profesor dueño del ciclo escolar puede actualizar parciales.
    """
    partial = db.query(Partial).filter(Partial.id == partial_id).first()
    
    if not partial:
        raise NotFoundError("Parcial", str(partial_id))
    
    # Obtener el ciclo escolar asociado
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == partial.school_cycle_id
    ).first()
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este parcial. Solo el profesor dueño del ciclo puede actualizar parciales."
        )
    
    # Si se está cambiando el school_cycle_id, verificar que el nuevo ciclo existe y pertenece al profesor
    if partial_data.school_cycle_id is not None and partial_data.school_cycle_id != partial.school_cycle_id:
        new_cycle = db.query(SchoolCycle).filter(
            SchoolCycle.id == partial_data.school_cycle_id
        ).first()
        
        if not new_cycle:
            raise NotFoundError("Ciclo escolar", str(partial_data.school_cycle_id))
        
        if new_cycle.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para mover este parcial a ese ciclo escolar. Solo puedes moverlo a ciclos que te pertenecen."
            )
    
    # Actualizar los campos
    update_data = partial_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(partial, field, value)
    
    db.commit()
    db.refresh(partial)
    
    partial_response = PartialResponse.model_validate(partial)
    return success_response(data=partial_response)


@router.delete("/{partial_id}", response_model=GenericResponse[None])
async def delete_partial(
    partial_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Elimina un parcial.
    Solo el profesor dueño del ciclo escolar puede eliminar parciales.
    """
    partial = db.query(Partial).filter(Partial.id == partial_id).first()
    
    if not partial:
        raise NotFoundError("Parcial", str(partial_id))
    
    # Obtener el ciclo escolar asociado
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == partial.school_cycle_id
    ).first()
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este parcial. Solo el profesor dueño del ciclo puede eliminar parciales."
        )
    
    db.delete(partial)
    db.commit()
    
    return success_response(data=None)

