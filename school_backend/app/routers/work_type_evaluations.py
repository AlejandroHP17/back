"""
Router para gestión de pesos de evaluación de tipos de trabajo.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import get_db
from app.models.work_type_evaluation import WorkTypeEvaluation
from app.models.cycle import SchoolCycle
from app.models.formative_field import FormativeField
from app.models.partial import Partial
from app.models.work_type import WorkType
from app.models.user import User
from app.schemas.work_type_evaluation import (
    WorkTypeEvaluationCreate,
    WorkTypeEvaluationUpdate,
    WorkTypeEvaluationResponse
)
from app.schemas.response import GenericResponse, success_response, created_response
from app.dependencies import get_current_active_user
from app.exceptions import NotFoundError, ConflictError

router = APIRouter(
    prefix="/work-type-evaluations",
    tags=["work-type-evaluations"]
)


@router.post("/", response_model=GenericResponse[WorkTypeEvaluationResponse], status_code=status.HTTP_201_CREATED)
async def create_work_type_evaluation(
    eval_data: WorkTypeEvaluationCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Crea un nuevo peso de evaluación.
    Solo el profesor dueño del ciclo escolar puede crear pesos de evaluación.
    """
    # Verificar que el campo formativo existe
    formative_field = db.query(FormativeField).filter(
        FormativeField.id == eval_data.formative_field_id
    ).first()
    
    if not formative_field:
        raise NotFoundError("Campo formativo", str(eval_data.formative_field_id))
    
    # Verificar que el parcial existe
    partial = db.query(Partial).filter(
        Partial.id == eval_data.partial_id
    ).first()
    
    if not partial:
        raise NotFoundError("Parcial", str(eval_data.partial_id))
    
    # Verificar que el tipo de trabajo existe
    work_type = db.query(WorkType).filter(
        WorkType.id == eval_data.work_type_id
    ).first()
    
    if not work_type:
        raise NotFoundError("Tipo de trabajo", str(eval_data.work_type_id))
    
    # Verificar que el campo formativo y el parcial pertenecen al mismo ciclo escolar
    if formative_field.school_cycle_id != partial.school_cycle_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El campo formativo y el parcial deben pertenecer al mismo ciclo escolar."
        )
    
    # Obtener el ciclo escolar
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == formative_field.school_cycle_id
    ).first()
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para crear pesos de evaluación en este ciclo escolar. Solo el profesor dueño del ciclo puede crear pesos de evaluación."
        )
    
    # Verificar que no existe ya una evaluación para esta combinación
    existing_eval = db.query(WorkTypeEvaluation).filter(
        and_(
            WorkTypeEvaluation.formative_field_id == eval_data.formative_field_id,
            WorkTypeEvaluation.partial_id == eval_data.partial_id,
            WorkTypeEvaluation.work_type_id == eval_data.work_type_id
        )
    ).first()
    
    if existing_eval:
        raise ConflictError("Ya existe un peso de evaluación para esta combinación de campo formativo, parcial y tipo de trabajo")
    
    # Crear el peso de evaluación
    new_eval = WorkTypeEvaluation(
        formative_field_id=eval_data.formative_field_id,
        partial_id=eval_data.partial_id,
        work_type_id=eval_data.work_type_id,
        evaluation_weight=eval_data.evaluation_weight
    )
    
    db.add(new_eval)
    db.commit()
    db.refresh(new_eval)
    
    eval_response = WorkTypeEvaluationResponse.model_validate(new_eval)
    return created_response(data=eval_response)


@router.get("/", response_model=GenericResponse[List[WorkTypeEvaluationResponse]])
async def list_work_type_evaluations(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    formative_field_id: int = Query(None, description="Filtrar por ID de campo formativo"),
    partial_id: int = Query(None, description="Filtrar por ID de parcial"),
    work_type_id: int = Query(None, description="Filtrar por ID de tipo de trabajo"),
    school_cycle_id: int = Query(None, description="Filtrar por ID de ciclo escolar"),
    teacher_id: int = Query(None, description="Filtrar por ID de profesor (solo ciclos del profesor)")
):
    """
    Lista todos los pesos de evaluación con filtros y paginación.
    """
    query = db.query(WorkTypeEvaluation)
    
    # Si se especifica teacher_id, filtrar por ciclos del profesor
    if teacher_id:
        query = query.join(FormativeField).join(SchoolCycle).filter(
            SchoolCycle.teacher_id == teacher_id
        )
    
    # Si se especifica school_cycle_id, filtrar por ciclo
    if school_cycle_id:
        query = query.join(FormativeField).filter(
            FormativeField.school_cycle_id == school_cycle_id
        )
    
    # Si se especifica formative_field_id, filtrar por campo formativo
    if formative_field_id:
        query = query.filter(WorkTypeEvaluation.formative_field_id == formative_field_id)
    
    # Si se especifica partial_id, filtrar por parcial
    if partial_id:
        query = query.filter(WorkTypeEvaluation.partial_id == partial_id)
    
    # Si se especifica work_type_id, filtrar por tipo de trabajo
    if work_type_id:
        query = query.filter(WorkTypeEvaluation.work_type_id == work_type_id)
    
    evaluations = query.offset(skip).limit(limit).all()
    evaluations_list = [WorkTypeEvaluationResponse.model_validate(eval) for eval in evaluations]
    return success_response(data=evaluations_list)


@router.get("/{evaluation_id}", response_model=GenericResponse[WorkTypeEvaluationResponse])
async def get_work_type_evaluation(
    evaluation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene un peso de evaluación por ID.
    """
    evaluation = db.query(WorkTypeEvaluation).filter(
        WorkTypeEvaluation.id == evaluation_id
    ).first()
    
    if not evaluation:
        raise NotFoundError("Peso de evaluación", str(evaluation_id))
    
    eval_response = WorkTypeEvaluationResponse.model_validate(evaluation)
    return success_response(data=eval_response)


@router.put("/{evaluation_id}", response_model=GenericResponse[WorkTypeEvaluationResponse])
async def update_work_type_evaluation(
    evaluation_id: int,
    eval_data: WorkTypeEvaluationUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Actualiza un peso de evaluación.
    Solo el profesor dueño del ciclo escolar puede actualizar pesos de evaluación.
    """
    evaluation = db.query(WorkTypeEvaluation).filter(
        WorkTypeEvaluation.id == evaluation_id
    ).first()
    
    if not evaluation:
        raise NotFoundError("Peso de evaluación", str(evaluation_id))
    
    # Obtener el campo formativo asociado
    formative_field = db.query(FormativeField).filter(
        FormativeField.id == evaluation.formative_field_id
    ).first()
    
    # Obtener el ciclo escolar
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == formative_field.school_cycle_id
    ).first()
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este peso de evaluación. Solo el profesor dueño del ciclo puede actualizar pesos de evaluación."
        )
    
    # Si se está cambiando alguno de los IDs, validar
    update_data = eval_data.model_dump(exclude_unset=True)
    
    new_formative_field_id = update_data.get("formative_field_id", evaluation.formative_field_id)
    new_partial_id = update_data.get("partial_id", evaluation.partial_id)
    new_work_type_id = update_data.get("work_type_id", evaluation.work_type_id)
    
    # Si se están cambiando los IDs, verificar que la nueva combinación no existe ya
    if (new_formative_field_id != evaluation.formative_field_id or 
        new_partial_id != evaluation.partial_id or 
        new_work_type_id != evaluation.work_type_id):
        
        # Verificar que el nuevo campo formativo existe
        if new_formative_field_id != evaluation.formative_field_id:
            new_formative_field = db.query(FormativeField).filter(
                FormativeField.id == new_formative_field_id
            ).first()
            if not new_formative_field:
                raise NotFoundError("Campo formativo", str(new_formative_field_id))
            
            # Verificar que pertenece al mismo profesor
            new_school_cycle = db.query(SchoolCycle).filter(
                SchoolCycle.id == new_formative_field.school_cycle_id
            ).first()
            if new_school_cycle.teacher_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para mover este peso de evaluación a ese campo formativo."
                )
        
        # Verificar que el nuevo parcial existe
        if new_partial_id != evaluation.partial_id:
            new_partial = db.query(Partial).filter(
                Partial.id == new_partial_id
            ).first()
            if not new_partial:
                raise NotFoundError("Parcial", str(new_partial_id))
            
            # Verificar que pertenece al mismo profesor
            new_school_cycle = db.query(SchoolCycle).filter(
                SchoolCycle.id == new_partial.school_cycle_id
            ).first()
            if new_school_cycle.teacher_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para mover este peso de evaluación a ese parcial."
                )
        
        # Verificar que el campo formativo y el parcial pertenecen al mismo ciclo
        if new_formative_field_id != evaluation.formative_field_id or new_partial_id != evaluation.partial_id:
            new_formative_field = db.query(FormativeField).filter(
                FormativeField.id == new_formative_field_id
            ).first()
            new_partial = db.query(Partial).filter(
                Partial.id == new_partial_id
            ).first()
            
            if new_formative_field.school_cycle_id != new_partial.school_cycle_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El campo formativo y el parcial deben pertenecer al mismo ciclo escolar."
                )
        
        # Verificar que no existe ya una evaluación para esta nueva combinación
        existing_eval = db.query(WorkTypeEvaluation).filter(
            and_(
                WorkTypeEvaluation.formative_field_id == new_formative_field_id,
                WorkTypeEvaluation.partial_id == new_partial_id,
                WorkTypeEvaluation.work_type_id == new_work_type_id,
                WorkTypeEvaluation.id != evaluation_id
            )
        ).first()
        
        if existing_eval:
            raise ConflictError("Ya existe un peso de evaluación para esta combinación de campo formativo, parcial y tipo de trabajo")
    
    # Actualizar los campos
    for field_key, value in update_data.items():
        setattr(evaluation, field_key, value)
    
    db.commit()
    db.refresh(evaluation)
    
    eval_response = WorkTypeEvaluationResponse.model_validate(evaluation)
    return success_response(data=eval_response)


@router.delete("/{evaluation_id}", response_model=GenericResponse[None])
async def delete_work_type_evaluation(
    evaluation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Elimina un peso de evaluación.
    Solo el profesor dueño del ciclo escolar puede eliminar pesos de evaluación.
    """
    evaluation = db.query(WorkTypeEvaluation).filter(
        WorkTypeEvaluation.id == evaluation_id
    ).first()
    
    if not evaluation:
        raise NotFoundError("Peso de evaluación", str(evaluation_id))
    
    # Obtener el campo formativo asociado
    formative_field = db.query(FormativeField).filter(
        FormativeField.id == evaluation.formative_field_id
    ).first()
    
    # Obtener el ciclo escolar
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == formative_field.school_cycle_id
    ).first()
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este peso de evaluación. Solo el profesor dueño del ciclo puede eliminar pesos de evaluación."
        )
    
    db.delete(evaluation)
    db.commit()
    
    return success_response(data=None)

