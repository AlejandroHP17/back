"""
Router para gestión de tipos de trabajo.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.database import get_db
from app.models.work_type import WorkType
from app.models.work_type_evaluation import WorkTypeEvaluation
from app.models.formative_field import FormativeField
from app.models.user import User
from app.schemas.work_type import (
    WorkTypeCreate,
    WorkTypeUpdate,
    WorkTypeResponse
)
from app.schemas.work_type_detail import (
    WorkTypeDetail,
    WorkTypeDetailResponse  
)


from app.schemas.response import GenericResponse, success_response, created_response
from app.dependencies import get_current_active_user
from app.exceptions import NotFoundError, ConflictError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/work-types",
    tags=["work-types"]
)


@router.post("/", response_model=GenericResponse[WorkTypeResponse], status_code=status.HTTP_201_CREATED)
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
        work_type_response = WorkTypeResponse.model_validate(new_work_type)
        return created_response(data=work_type_response)
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


@router.get("/", response_model=GenericResponse[List[WorkTypeResponse]])
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
    work_types_list = [WorkTypeResponse.model_validate(wt) for wt in work_types]
    return success_response(data=work_types_list)


@router.get("/{work_type_id}", response_model=GenericResponse[WorkTypeResponse])
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
    
    work_type_response = WorkTypeResponse.model_validate(work_type)
    return success_response(data=work_type_response)


@router.put("/{work_type_id}", response_model=GenericResponse[WorkTypeResponse])
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
        work_type_response = WorkTypeResponse.model_validate(work_type)
        return success_response(data=work_type_response)
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


@router.delete("/{work_type_id}", response_model=GenericResponse[str])
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
        return success_response(data="El elemento se ha borrado correctamente")
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

@router.get("/by_formative_field/{formative_field_id}", response_model=GenericResponse[WorkTypeDetail])
async def get_work_types_by_formative_field(
    formative_field_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene los tipos de trabajo y su peso de evaluación asociados a un campo formativo.
    """
    # 1. Verificar que el campo formativo existe
    formative_field = db.query(FormativeField).filter(FormativeField.id == formative_field_id).first()
    if not formative_field:
        raise NotFoundError("Campo formativo", str(formative_field_id))
    
    # 2. Obtener TODAS las evaluaciones (WorkTypeEvaluation) asociadas al campo formativo
    # Esto incluye duplicados si un WorkType se evalúa en varios parciales.
    evaluations = db.query(WorkTypeEvaluation).filter(
        WorkTypeEvaluation.formative_field_id == formative_field.id
    ).join(WorkType).order_by(WorkType.name).all()
    
    # 3. Agrupar/Desduplicar WorkTypes:
    # Usamos un diccionario para quedarnos solo con un registro por WorkType (el primero que encuentre).
    work_types_map = {} 
    
    for eval_item in evaluations:
        if eval_item.work_type_id not in work_types_map:
            # Crear el esquema de respuesta WorkTypeDetailResponse usando Pydantic
            work_type_detail = WorkTypeDetailResponse(
                # Nota: Asumo que el modelo WorkTypeDetailResponse fue corregido para usar aliases
                # (id -> work_type_id, name -> work_type_name) si era necesario, o si
                # tu modelo de DB WorkType tiene los nombres correctos.
                work_type_id=eval_item.work_type_id,
                work_type_name=eval_item.work_type.name, # Accede al nombre desde la relación JOIN
                evaluation_weight=eval_item.evaluation_weight
            )
            work_types_map[eval_item.work_type_id] = work_type_detail
            
    # 4. Convertir el mapa de work-types a la lista final
    work_types_list = list(work_types_map.values())
    
    # 5. Construir la respuesta final
    response_data = WorkTypeDetail(
        formative_field_id=formative_field_id,
        formative_field_name=formative_field.name,
        work_types=work_types_list # Ahora enviamos List[WorkTypeDetailResponse]
    )
    return success_response(data=response_data)