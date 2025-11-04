"""
Router para gestión de campos formativos.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.learning_field import FormativeField
from app.models.cycle import SchoolCycle
from app.models.user import User
from app.schemas.learning_field import (
    FormativeFieldCreate,
    FormativeFieldUpdate,
    FormativeFieldResponse
)
from app.dependencies import get_current_active_user
from app.exceptions import NotFoundError, ConflictError

router = APIRouter(
    prefix="/formative-fields",
    tags=["campos formativos"]
)


@router.post("/", response_model=FormativeFieldResponse, status_code=status.HTTP_201_CREATED)
async def create_formative_field(
    field_data: FormativeFieldCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Crea un nuevo campo formativo.
    Solo el profesor dueño del ciclo escolar puede crear campos formativos.
    """
    # Verificar que el ciclo escolar existe
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == field_data.school_cycle_id
    ).first()
    
    if not school_cycle:
        raise NotFoundError("Ciclo escolar", str(field_data.school_cycle_id))
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para crear campos formativos en este ciclo escolar. Solo el profesor dueño del ciclo puede crear campos formativos."
        )
    
    # Crear el campo formativo
    new_field = FormativeField(
        school_cycle_id=field_data.school_cycle_id,
        name=field_data.name,
        code=field_data.code
    )
    
    db.add(new_field)
    db.commit()
    db.refresh(new_field)
    
    return FormativeFieldResponse.model_validate(new_field)


@router.get("/", response_model=List[FormativeFieldResponse])
async def list_formative_fields(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    school_cycle_id: int = Query(None, description="Filtrar por ID de ciclo escolar"),
    teacher_id: int = Query(None, description="Filtrar por ID de profesor (solo ciclos del profesor)")
):
    """
    Lista todos los campos formativos con filtros y paginación.
    Si se especifica teacher_id, solo muestra campos formativos de ciclos pertenecientes a ese profesor.
    """
    query = db.query(FormativeField)
    
    # Si se especifica teacher_id, filtrar por ciclos del profesor
    if teacher_id:
        query = query.join(SchoolCycle).filter(SchoolCycle.teacher_id == teacher_id)
    
    # Si se especifica school_cycle_id, filtrar por ciclo
    if school_cycle_id:
        query = query.filter(FormativeField.school_cycle_id == school_cycle_id)
    
    fields = query.offset(skip).limit(limit).all()
    return [FormativeFieldResponse.model_validate(field) for field in fields]


@router.get("/{field_id}", response_model=FormativeFieldResponse)
async def get_formative_field(
    field_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene un campo formativo por ID.
    """
    field = db.query(FormativeField).filter(FormativeField.id == field_id).first()
    
    if not field:
        raise NotFoundError("Campo formativo", str(field_id))
    
    return FormativeFieldResponse.model_validate(field)


@router.put("/{field_id}", response_model=FormativeFieldResponse)
async def update_formative_field(
    field_id: int,
    field_data: FormativeFieldUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Actualiza un campo formativo.
    Solo el profesor dueño del ciclo escolar puede actualizar campos formativos.
    """
    field = db.query(FormativeField).filter(FormativeField.id == field_id).first()
    
    if not field:
        raise NotFoundError("Campo formativo", str(field_id))
    
    # Obtener el ciclo escolar asociado
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == field.school_cycle_id
    ).first()
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este campo formativo. Solo el profesor dueño del ciclo puede actualizar campos formativos."
        )
    
    # Si se está cambiando el school_cycle_id, verificar que el nuevo ciclo existe y pertenece al profesor
    if field_data.school_cycle_id is not None and field_data.school_cycle_id != field.school_cycle_id:
        new_cycle = db.query(SchoolCycle).filter(
            SchoolCycle.id == field_data.school_cycle_id
        ).first()
        
        if not new_cycle:
            raise NotFoundError("Ciclo escolar", str(field_data.school_cycle_id))
        
        if new_cycle.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para mover este campo formativo a ese ciclo escolar. Solo puedes moverlo a ciclos que te pertenecen."
            )
    
    # Actualizar los campos
    update_data = field_data.model_dump(exclude_unset=True)
    for field_key, value in update_data.items():
        setattr(field, field_key, value)
    
    db.commit()
    db.refresh(field)
    
    return FormativeFieldResponse.model_validate(field)


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_formative_field(
    field_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Elimina un campo formativo.
    Solo el profesor dueño del ciclo escolar puede eliminar campos formativos.
    """
    field = db.query(FormativeField).filter(FormativeField.id == field_id).first()
    
    if not field:
        raise NotFoundError("Campo formativo", str(field_id))
    
    # Obtener el ciclo escolar asociado
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == field.school_cycle_id
    ).first()
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este campo formativo. Solo el profesor dueño del ciclo puede eliminar campos formativos."
        )
    
    db.delete(field)
    db.commit()
    
    return None

