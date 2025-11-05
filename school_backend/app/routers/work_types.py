"""
Router para gestión de tipos de trabajo.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.database import get_db
from app.models.work_type import WorkType
from app.models.user import User
from app.schemas.work_type import (
    WorkTypeCreate,
    WorkTypeUpdate,
    WorkTypeResponse
)
from app.dependencies import get_current_active_user
from app.exceptions import NotFoundError, ConflictError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/work-types",
    tags=["work-types"]
)


@router.post("/", response_model=WorkTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_work_type(
    work_type_data: WorkTypeCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Crea un nuevo tipo de trabajo.
    Solo los profesores pueden crear tipos de trabajo.
    """
    # Verificar que el usuario es profesor
    if current_user.access_level_id not in [2, 3]:  # 2 = Profesor, 3 = Administrador
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los profesores pueden crear tipos de trabajo."
        )
    
    # Verificar que no existe ya un tipo de trabajo con el mismo nombre para este profesor
    existing_work_type = db.query(WorkType).filter(
        WorkType.teacher_id == current_user.id,
        WorkType.name == work_type_data.name
    ).first()
    
    if existing_work_type:
        raise ConflictError(f"Ya existe un tipo de trabajo con el nombre '{work_type_data.name}' para este profesor.")
    
    try:
        new_work_type = WorkType(
            teacher_id=current_user.id,
            name=work_type_data.name
        )
        db.add(new_work_type)
        db.commit()
        db.refresh(new_work_type)
        return WorkTypeResponse.model_validate(new_work_type)
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        logger.error(f"Error de integridad al crear tipo de trabajo: {error_msg}")
        if "uq_worktypes_teacher_name" in error_msg:
            raise ConflictError(f"Ya existe un tipo de trabajo con el nombre '{work_type_data.name}' para este profesor.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de integridad: {error_msg}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error de base de datos al crear tipo de trabajo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de base de datos: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado al crear tipo de trabajo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )


@router.get("/", response_model=List[WorkTypeResponse])
async def list_work_types(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    teacher_id: int = Query(None, description="Filtrar por ID de profesor")
):
    """
    Lista todos los tipos de trabajo con filtros y paginación.
    Si se especifica teacher_id, solo muestra tipos de trabajo de ese profesor.
    Si no se especifica, muestra los tipos de trabajo del profesor actual.
    """
    query = db.query(WorkType)
    
    # Si se especifica teacher_id, filtrar por profesor
    if teacher_id:
        query = query.filter(WorkType.teacher_id == teacher_id)
    else:
        # Por defecto, mostrar solo los tipos de trabajo del profesor actual
        query = query.filter(WorkType.teacher_id == current_user.id)
    
    work_types = query.offset(skip).limit(limit).all()
    return [WorkTypeResponse.model_validate(wt) for wt in work_types]


@router.get("/{work_type_id}", response_model=WorkTypeResponse)
async def get_work_type(
    work_type_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene un tipo de trabajo por ID.
    """
    work_type = db.query(WorkType).filter(WorkType.id == work_type_id).first()
    
    if not work_type:
        raise NotFoundError("Tipo de trabajo", str(work_type_id))
    
    return WorkTypeResponse.model_validate(work_type)


@router.put("/{work_type_id}", response_model=WorkTypeResponse)
async def update_work_type(
    work_type_id: int,
    work_type_data: WorkTypeUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Actualiza un tipo de trabajo.
    Solo el profesor dueño del tipo de trabajo puede actualizarlo.
    """
    work_type = db.query(WorkType).filter(WorkType.id == work_type_id).first()
    
    if not work_type:
        raise NotFoundError("Tipo de trabajo", str(work_type_id))
    
    # Verificar que el usuario es el profesor dueño del tipo de trabajo
    if work_type.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este tipo de trabajo. Solo el profesor dueño puede actualizarlo."
        )
    
    update_data = work_type_data.model_dump(exclude_unset=True)
    
    # Si se está cambiando el nombre, verificar que no existe ya otro tipo con ese nombre
    if "name" in update_data and update_data["name"] != work_type.name:
        existing_work_type = db.query(WorkType).filter(
            WorkType.teacher_id == current_user.id,
            WorkType.name == update_data["name"],
            WorkType.id != work_type_id
        ).first()
        
        if existing_work_type:
            raise ConflictError(f"Ya existe un tipo de trabajo con el nombre '{update_data['name']}' para este profesor.")
    
    try:
        for field_key, value in update_data.items():
            setattr(work_type, field_key, value)
        
        db.commit()
        db.refresh(work_type)
        return WorkTypeResponse.model_validate(work_type)
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        logger.error(f"Error de integridad al actualizar tipo de trabajo: {error_msg}")
        if "uq_worktypes_teacher_name" in error_msg:
            raise ConflictError(f"Ya existe un tipo de trabajo con el nombre '{update_data.get('name', work_type.name)}' para este profesor.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de integridad: {error_msg}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error de base de datos al actualizar tipo de trabajo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de base de datos: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado al actualizar tipo de trabajo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )


@router.delete("/{work_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_type(
    work_type_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Elimina un tipo de trabajo.
    Solo el profesor dueño del tipo de trabajo puede eliminarlo.
    """
    work_type = db.query(WorkType).filter(WorkType.id == work_type_id).first()
    
    if not work_type:
        raise NotFoundError("Tipo de trabajo", str(work_type_id))
    
    # Verificar que el usuario es el profesor dueño del tipo de trabajo
    if work_type.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este tipo de trabajo. Solo el profesor dueño puede eliminarlo."
        )
    
    try:
        db.delete(work_type)
        db.commit()
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error de base de datos al eliminar tipo de trabajo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de base de datos: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado al eliminar tipo de trabajo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )

