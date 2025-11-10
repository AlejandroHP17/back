"""
Router para gestión de campos formativos.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.formative_field import FormativeField
from app.models.cycle import SchoolCycle
from app.models.work_type import WorkType
from app.models.work_type_evaluation import WorkTypeEvaluation
from app.models.student_work import StudentWork
from app.models.partial import Partial
from app.models.user import User
from app.schemas.formative_field import (
    FormativeFieldCreate,
    FormativeFieldUpdate,
    FormativeFieldResponse
)
from app.schemas.formative_field_bulk import FormativeFieldBulkCreate
from decimal import Decimal
from app.schemas.response import GenericResponse, success_response, created_response
from app.dependencies import get_current_active_user
from app.exceptions import NotFoundError, ConflictError

router = APIRouter(
    prefix="/formative-fields",
    tags=["formative-fields"]
)


@router.post("/", response_model=GenericResponse[FormativeFieldResponse], status_code=status.HTTP_201_CREATED)
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
    
    field_response = FormativeFieldResponse.model_validate(new_field)
    return created_response(data=field_response)


@router.get("/", response_model=GenericResponse[List[FormativeFieldResponse]])
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
    fields_list = [FormativeFieldResponse.model_validate(field) for field in fields]
    return success_response(data=fields_list)


@router.get("/{field_id}", response_model=GenericResponse[FormativeFieldResponse])
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
    
    field_response = FormativeFieldResponse.model_validate(field)
    return success_response(data=field_response)


@router.put("/{field_id}", response_model=GenericResponse[FormativeFieldResponse])
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
    
    field_response = FormativeFieldResponse.model_validate(field)
    return success_response(data=field_response)


@router.delete("/{field_id}", response_model=GenericResponse[str])
async def delete_formative_field(
    field_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Elimina un campo formativo.
    Solo el profesor dueño del ciclo escolar puede eliminar campos formativos.
    Elimina automáticamente los registros relacionados (evaluaciones y trabajos de estudiantes).
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
    
    try:
        # Eliminar primero los registros relacionados: work_type_evaluations
        evaluations = db.query(WorkTypeEvaluation).filter(
            WorkTypeEvaluation.formative_field_id == field_id
        ).all()
        for eval_item in evaluations:
            db.delete(eval_item)
        
        # Eliminar los registros relacionados: student_works
        student_works = db.query(StudentWork).filter(
            StudentWork.formative_field_id == field_id
        ).all()
        for work in student_works:
            db.delete(work)
        
        # Finalmente eliminar el campo formativo
        db.delete(field)
        db.commit()
        
        return success_response(data="El elemento se ha borrado correctamente")
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el campo formativo: {str(e)}"
        )


@router.post("/bulk", response_model=GenericResponse[FormativeFieldResponse], status_code=status.HTTP_201_CREATED)
async def create_formative_field_bulk(
    bulk_data: FormativeFieldBulkCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Crea un campo formativo con work-types y evaluaciones en una sola operación.
    
    Flujo:
    1. Crea el campo formativo (ej: "Español", "Matemáticas")
    2. Crea work-types nuevos o usa existentes (pueden ser "tareas", "examen", etc.)
    3. Crea evaluaciones con porcentajes para los work-types nuevos
    
    Los work-types pueden ser:
    - Nuevos: se crean con el nombre proporcionado
    - Existentes: se usan por ID (deben pertenecer al profesor autenticado)
    
    Las evaluaciones solo se crean para work-types nuevos.
    """
    # Verificar que el ciclo escolar existe y pertenece al profesor
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == bulk_data.school_cycle_id
    ).first()
    
    if not school_cycle:
        raise NotFoundError("Ciclo escolar", str(bulk_data.school_cycle_id))
    
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para crear campos formativos en este ciclo escolar."
        )
    
    # Validar work-types: si tiene ID, debe existir y pertenecer al profesor; si no tiene ID, debe tener nombre
    work_type_map = {}  # Mapeo de nombre -> ID para work-types nuevos
    existing_work_type_ids = set()
    
    for wt_item in bulk_data.work_types:
        if wt_item.id is not None:
            # Verificar que el work-type existente pertenece al profesor
            existing_wt = db.query(WorkType).filter(
                WorkType.id == wt_item.id,
                WorkType.teacher_id == current_user.id
            ).first()
            
            if not existing_wt:
                raise NotFoundError(f"Work-type con ID {wt_item.id}", "No existe o no pertenece al profesor")
            
            existing_work_type_ids.add(wt_item.id)
        else:
            # Work-type nuevo: debe tener nombre
            if not wt_item.name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Los work-types nuevos deben tener un nombre"
                )
            
            # Verificar que no existe ya un work-type con ese nombre para este profesor
            existing_wt = db.query(WorkType).filter(
                WorkType.name == wt_item.name,
                WorkType.teacher_id == current_user.id
            ).first()
            
            if existing_wt:
                raise ConflictError(f"Ya existe un work-type con el nombre '{wt_item.name}' para este profesor. Usa el ID {existing_wt.id} en su lugar.")
    
    # Crear el campo formativo
    new_field = FormativeField(
        school_cycle_id=bulk_data.school_cycle_id,
        name=bulk_data.name,
        code=bulk_data.code
    )
    db.add(new_field)
    db.flush()  # Para obtener el ID sin hacer commit
    
    # Crear work-types nuevos
    for wt_item in bulk_data.work_types:
        if wt_item.id is None:
            # Crear nuevo work-type
            new_wt = WorkType(
                teacher_id=current_user.id,
                name=wt_item.name
            )
            db.add(new_wt)
            db.flush()  # Para obtener el ID
            work_type_map[wt_item.name] = new_wt.id
    
    # Validar y crear evaluaciones
    for eval_item in bulk_data.evaluations:
        # Verificar que el work-type_name corresponde a un work-type nuevo
        if eval_item.work_type_name not in work_type_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El work-type '{eval_item.work_type_name}' no es un work-type nuevo. Las evaluaciones solo se pueden crear para work-types nuevos."
            )
        
        work_type_id = work_type_map[eval_item.work_type_name]
        
        # Verificar que el partial existe y pertenece al mismo ciclo escolar
        partial = db.query(Partial).filter(Partial.id == eval_item.partial_id).first()
        
        if not partial:
            raise NotFoundError("Parcial", str(eval_item.partial_id))
        
        if partial.school_cycle_id != bulk_data.school_cycle_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El parcial {eval_item.partial_id} no pertenece al ciclo escolar {bulk_data.school_cycle_id}"
            )
        
        # Verificar que no existe ya una evaluación para esta combinación
        existing_eval = db.query(WorkTypeEvaluation).filter(
            WorkTypeEvaluation.formative_field_id == new_field.id,
            WorkTypeEvaluation.partial_id == eval_item.partial_id,
            WorkTypeEvaluation.work_type_id == work_type_id
        ).first()
        
        if existing_eval:
            raise ConflictError(
                f"Ya existe una evaluación para el campo formativo '{bulk_data.name}', "
                f"parcial {eval_item.partial_id} y work-type '{eval_item.work_type_name}'"
            )
        
        # Crear la evaluación
        new_eval = WorkTypeEvaluation(
            formative_field_id=new_field.id,
            partial_id=eval_item.partial_id,
            work_type_id=work_type_id,
            evaluation_weight=Decimal(str(eval_item.evaluation_weight))
        )
        db.add(new_eval)
    
    # Hacer commit de todo
    db.commit()
    db.refresh(new_field)
    
    field_response = FormativeFieldResponse.model_validate(new_field)
    return created_response(data=field_response)

