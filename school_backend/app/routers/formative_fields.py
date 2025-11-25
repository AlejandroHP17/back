"""
Router para gestión de campos formativos.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.database import get_db
from app.models.formative_field import FormativeField
from app.models.cycle import SchoolCycle
from app.models.work_type import WorkType
from app.models.work_type_evaluation import WorkTypeEvaluation
from app.models.student_work import StudentWork
from app.models.partial import Partial
from app.models.user import User
from app.models.catalog import School
from app.schemas.formative_field import (
    FormativeFieldCreate,
    FormativeFieldUpdate,
    FormativeFieldResponse,
    FormativeFieldCreateResponse
)
from app.schemas.formative_field_bulk import FormativeFieldBulkCreate
from app.schemas.formative_field_detail import FormativeFieldsByCycleResponse, FormativeFieldDetail, WorkTypeDetail
from decimal import Decimal
from app.schemas.response import GenericResponse, success_response, created_response
from app.dependencies import get_current_active_user
from app.exceptions import NotFoundError, ConflictError

router = APIRouter(
    prefix="/formative-fields",
    tags=["formative-fields"]
)


@router.post("/", response_model=GenericResponse[FormativeFieldCreateResponse], status_code=status.HTTP_201_CREATED)
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
    
    field_response = FormativeFieldCreateResponse.model_validate(new_field)
    return created_response(data=field_response)


@router.get("/by-cycle/{school_cycle_id}", response_model=GenericResponse[FormativeFieldsByCycleResponse])
async def get_formative_fields_by_cycle(
    school_cycle_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene todos los campos formativos de un ciclo escolar con sus work-types y pesos de evaluación.
    Retorna los campos formativos agrupados con sus work-types asociados.
    """
    # Verificar que el ciclo escolar existe
    school_cycle = db.query(SchoolCycle).filter(SchoolCycle.id == school_cycle_id).first()
    if not school_cycle:
        raise NotFoundError("Ciclo escolar", str(school_cycle_id))
    
    # Obtener todos los campos formativos del ciclo escolar
    formative_fields = db.query(FormativeField).filter(
        FormativeField.school_cycle_id == school_cycle_id
    ).order_by(FormativeField.name).all()
    
    # Construir la respuesta con work-types
    formative_fields_detail = []
    
    for field in formative_fields:
        # Obtener todas las evaluaciones de este campo formativo con sus work-types
        evaluations = db.query(WorkTypeEvaluation).filter(
            WorkTypeEvaluation.formative_field_id == field.id
        ).join(WorkType).order_by(WorkType.name).all()
        
        # Agrupar work-types únicos (un work-type puede tener múltiples evaluaciones en diferentes parciales)
        # Usaremos un diccionario para evitar duplicados por work_type_id
        work_types_map = {}  # work_type_id -> WorkTypeDetail
        
        for eval_item in evaluations:
            # Si el work_type ya está en el mapa, lo saltamos (mantenemos el primero encontrado)
            # O si quieres el promedio, podrías calcularlo aquí
            if eval_item.work_type_id not in work_types_map:
                work_type_detail = WorkTypeDetail(
                    work_type_id=eval_item.work_type_id,
                    work_type_name=eval_item.work_type.name,
                    evaluation_weight=eval_item.evaluation_weight
                )
                work_types_map[eval_item.work_type_id] = work_type_detail
        
        # Convertir el diccionario a lista
        work_types_detail = list(work_types_map.values())
        
        # Crear el detalle del campo formativo
        field_detail = FormativeFieldDetail(
            formative_field_id=field.id,
            name=field.name,
            code=field.code,
            work_types=work_types_detail
        )
        formative_fields_detail.append(field_detail)
    
    # Construir la respuesta
    response_data = FormativeFieldsByCycleResponse(
        school_cycle_id=school_cycle_id,
        formative_fields=formative_fields_detail
    )
    
    return success_response(data=response_data)


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
    
    # Cargar relaciones necesarias
    fields = query.options(
        joinedload(FormativeField.school_cycle)
    ).offset(skip).limit(limit).all()
    
    # Construir respuestas con nombres
    fields_list = []
    for field in fields:
        school = field.school_cycle.school if field.school_cycle and field.school_cycle.school else None
        
        field_dict = {
            "id": field.id,
            "school_cycle_id": field.school_cycle_id,
            "name": field.name,
            "code": field.code,
            "created_at": field.created_at,
            "school_cycle_name": field.school_cycle.name if field.school_cycle else None,
            "school_name": school.name if school else None
        }
        fields_list.append(FormativeFieldResponse.model_validate(field_dict))
    
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
    field = db.query(FormativeField).options(
        joinedload(FormativeField.school_cycle)
    ).filter(FormativeField.id == field_id).first()
    
    if not field:
        raise NotFoundError("Campo formativo", str(field_id))
    
    school = field.school_cycle.school if field.school_cycle and field.school_cycle.school else None
    
    field_dict = {
        "id": field.id,
        "school_cycle_id": field.school_cycle_id,
        "name": field.name,
        "code": field.code,
        "created_at": field.created_at,
        "school_cycle_name": field.school_cycle.name if field.school_cycle else None,
        "school_name": school.name if school else None
    }
    field_response = FormativeFieldResponse.model_validate(field_dict)
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
    
    # Recargar con relaciones
    field = db.query(FormativeField).options(
        joinedload(FormativeField.school_cycle)
    ).filter(FormativeField.id == field_id).first()
    
    school = field.school_cycle.school if field.school_cycle and field.school_cycle.school else None
    
    field_dict = {
        "id": field.id,
        "school_cycle_id": field.school_cycle_id,
        "name": field.name,
        "code": field.code,
        "created_at": field.created_at,
        "school_cycle_name": field.school_cycle.name if field.school_cycle else None,
        "school_name": school.name if school else None
    }
    field_response = FormativeFieldResponse.model_validate(field_dict)
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


@router.post("/bulk", response_model=GenericResponse[FormativeFieldCreateResponse], status_code=status.HTTP_201_CREATED)
async def create_formative_field_bulk(
    bulk_data: FormativeFieldBulkCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Crea un campo formativo con work-types y evaluaciones en una sola operación.
    
    Flujo:
    1. Crea el campo formativo (ej: "Español", "Matemáticas")
    2. Crea work-types nuevos o reutiliza existentes (pueden ser "tareas", "examen", etc.)
    3. Crea evaluaciones con porcentajes para los work-types (nuevos o existentes)
    
    Los work-types:
    - Si existe por nombre para el profesor: se reutiliza (no se crea duplicado)
    - Si no existe: se crea uno nuevo con el nombre proporcionado
    - Si se proporciona ID: se usa el existente (debe pertenecer al profesor)
    
    Las evaluaciones se pueden crear para work-types nuevos o existentes.
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
    
    # Mapeo de nombre -> ID para todos los work-types (nuevos y existentes)
    work_type_name_to_id = {}  # Mapeo de nombre -> ID
    valid_work_type_ids = set()  # Set de IDs válidos
    
    # Primero, procesar todos los work-types para construir el mapa
    for wt_item in bulk_data.work_types:
        if wt_item.id is not None:
            # Verificar que el work-type existente pertenece al profesor
            existing_wt = db.query(WorkType).filter(
                WorkType.id == wt_item.id,
                WorkType.teacher_id == current_user.id
            ).first()
            
            if not existing_wt:
                raise NotFoundError(f"Work-type con ID {wt_item.id}", "No existe o no pertenece al profesor")
            
            # Agregar al mapa y al set
            work_type_name_to_id[existing_wt.name] = existing_wt.id
            valid_work_type_ids.add(existing_wt.id)
        else:
            # Work-type por nombre: debe tener nombre
            if not wt_item.name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Los work-types deben tener un nombre"
                )
            
            # Verificar si ya existe un work-type con ese nombre para este profesor
            existing_wt = db.query(WorkType).filter(
                WorkType.name == wt_item.name,
                WorkType.teacher_id == current_user.id
            ).first()
            
            if existing_wt:
                # Reutilizar el work-type existente
                work_type_name_to_id[wt_item.name] = existing_wt.id
                valid_work_type_ids.add(existing_wt.id)
            else:
                # Se creará uno nuevo más adelante, guardar el nombre para referencia
                work_type_name_to_id[wt_item.name] = None  # Marcador para crear nuevo
    
    # Crear el campo formativo
    new_field = FormativeField(
        school_cycle_id=bulk_data.school_cycle_id,
        name=bulk_data.name,
        code=bulk_data.code
    )
    db.add(new_field)
    db.flush()  # Para obtener el ID sin hacer commit
    
    # Crear work-types nuevos (solo los que no existen)
    for wt_item in bulk_data.work_types:
        if wt_item.id is None and wt_item.name in work_type_name_to_id and work_type_name_to_id[wt_item.name] is None:
            # Verificar nuevamente si existe (por si acaso)
            existing_wt = db.query(WorkType).filter(
                WorkType.name == wt_item.name,
                WorkType.teacher_id == current_user.id
            ).first()
            
            if not existing_wt:
                # Crear nuevo work-type
                new_wt = WorkType(
                    teacher_id=current_user.id,
                    name=wt_item.name
                )
                db.add(new_wt)
                db.flush()  # Para obtener el ID
                work_type_name_to_id[wt_item.name] = new_wt.id
                valid_work_type_ids.add(new_wt.id)
            else:
                # Si existe, actualizar el mapa
                work_type_name_to_id[wt_item.name] = existing_wt.id
                valid_work_type_ids.add(existing_wt.id)
    
    # Validar y crear evaluaciones
    for eval_item in bulk_data.evaluations:
        # Determinar el work_type_id: si es null, buscar por nombre
        if eval_item.work_type_id is not None:
            # Usar el ID proporcionado
            work_type_id = eval_item.work_type_id
            
            # Verificar que el work_type_id está en el set de IDs válidos
            if work_type_id not in valid_work_type_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El work-type con ID {work_type_id} no está en la lista de work-types proporcionados."
                )
        else:
            # Buscar por nombre
            if not eval_item.work_type_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Debe proporcionar work_type_id o work_type_name en la evaluación."
                )
            
            # Verificar que el nombre está en el mapa
            if eval_item.work_type_name not in work_type_name_to_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El work-type '{eval_item.work_type_name}' no está en la lista de work-types proporcionados."
                )
            
            work_type_id = work_type_name_to_id[eval_item.work_type_name]
            
            if work_type_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error interno: el work-type '{eval_item.work_type_name}' no tiene ID asignado."
                )
        
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
                f"parcial {eval_item.partial_id} y work-type ID {eval_item.work_type_id}"
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
    
    field_response = FormativeFieldCreateResponse.model_validate(new_field)
    return created_response(data=field_response)

