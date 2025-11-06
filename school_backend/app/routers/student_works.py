"""
Router para gestión de trabajos de estudiantes.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date
from app.database import get_db
from app.models.student_work import StudentWork
from app.models.student import Student
from app.models.cycle import SchoolCycle
from app.models.partial import Partial
from app.models.formative_field import FormativeField
from app.models.work_type import WorkType
from app.models.user import User
from app.schemas.student_work import (
    StudentWorkCreate,
    StudentWorkUpdate,
    StudentWorkResponse,
    StudentWorkBulkCreate,
    StudentWorkBulkResponse
)
from app.schemas.response import GenericResponse, success_response, created_response
from app.dependencies import get_current_active_user
from app.exceptions import NotFoundError, ConflictError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/student-works",
    tags=["student-works"]
)


@router.post("/bulk", response_model=GenericResponse[StudentWorkBulkResponse], status_code=status.HTTP_201_CREATED)
async def create_student_works_bulk(
    bulk_data: StudentWorkBulkCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Crea trabajos de estudiantes en masa.
    Si un estudiante no viene en la lista de grades, se crea el trabajo con grade=null.
    Solo el profesor dueño del ciclo escolar puede crear trabajos.
    """
    # Verificar que el campo formativo existe
    formative_field = db.query(FormativeField).filter(
        FormativeField.id == bulk_data.formative_field_id
    ).first()
    if not formative_field:
        raise NotFoundError("Campo formativo", str(bulk_data.formative_field_id))
    
    # Verificar que el parcial existe
    partial = db.query(Partial).filter(
        Partial.id == bulk_data.partial_id
    ).first()
    if not partial:
        raise NotFoundError("Parcial", str(bulk_data.partial_id))
    
    # Verificar que el tipo de trabajo existe
    work_type = db.query(WorkType).filter(
        WorkType.id == bulk_data.work_type_id
    ).first()
    if not work_type:
        raise NotFoundError("Tipo de trabajo", str(bulk_data.work_type_id))
    
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
            detail="No tienes permiso para crear trabajos en este ciclo escolar. Solo el profesor dueño del ciclo puede crear trabajos."
        )
    
    # Si se especifica school_cycle_id, validar que coincide
    if bulk_data.school_cycle_id and bulk_data.school_cycle_id != school_cycle.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El school_cycle_id especificado no coincide con el ciclo escolar del campo formativo y parcial."
        )
    
    # Obtener todos los estudiantes activos del ciclo escolar
    all_students = db.query(Student).filter(
        Student.school_cycle_id == school_cycle.id,
        Student.is_active == True
    ).all()
    
    if not all_students:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron estudiantes activos en este ciclo escolar."
        )
    
    # Crear un diccionario de calificaciones por student_id
    grades_dict = {item.student_id: item.grade for item in bulk_data.grades}
    
    # Validar que todos los student_ids en grades existen y pertenecen al ciclo
    for student_id in grades_dict.keys():
        student = db.query(Student).filter(
            Student.id == student_id,
            Student.school_cycle_id == school_cycle.id
        ).first()
        if not student:
            raise NotFoundError("Estudiante", str(student_id))
    
    created_works = []
    updated_works = []
    
    # Procesar todos los estudiantes del ciclo
    for student in all_students:
        # Obtener la calificación si existe, sino será None
        grade = grades_dict.get(student.id, None)
        
        # Verificar si ya existe un trabajo para esta combinación
        existing_work = db.query(StudentWork).filter(
            and_(
                StudentWork.student_id == student.id,
                StudentWork.formative_field_id == bulk_data.formative_field_id,
                StudentWork.partial_id == bulk_data.partial_id,
                StudentWork.work_type_id == bulk_data.work_type_id,
                StudentWork.name == bulk_data.name
            )
        ).first()
        
        if existing_work:
            # Actualizar el trabajo existente
            existing_work.grade = grade
            if bulk_data.work_date:
                existing_work.work_date = bulk_data.work_date
            updated_works.append(existing_work)
        else:
            # Crear nuevo trabajo
            new_work = StudentWork(
                student_id=student.id,
                formative_field_id=bulk_data.formative_field_id,
                partial_id=bulk_data.partial_id,
                work_type_id=bulk_data.work_type_id,
                teacher_id=current_user.id,
                name=bulk_data.name,
                grade=grade,  # Puede ser None si el estudiante no está en la lista
                work_date=bulk_data.work_date
            )
            db.add(new_work)
            created_works.append(new_work)
    
    try:
        db.commit()
        
        # Refrescar los objetos para obtener los IDs generados
        for work in created_works:
            db.refresh(work)
        for work in updated_works:
            db.refresh(work)
        
        # Contar estudiantes con y sin calificación
        total_with_grade = sum(1 for work in created_works + updated_works if work.grade is not None)
        total_without_grade = len(created_works + updated_works) - total_with_grade
        
        bulk_response = StudentWorkBulkResponse(
            created=[StudentWorkResponse.model_validate(work) for work in created_works],
            updated=[StudentWorkResponse.model_validate(work) for work in updated_works],
            total_with_grade=total_with_grade,
            total_without_grade=total_without_grade,
            formative_field_id=bulk_data.formative_field_id,
            partial_id=bulk_data.partial_id,
            work_type_id=bulk_data.work_type_id,
            name=bulk_data.name
        )
        return created_response(data=bulk_response)
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear trabajos en masa: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear trabajos: {str(e)}"
        )


@router.post("/", response_model=GenericResponse[StudentWorkResponse], status_code=status.HTTP_201_CREATED)
async def create_student_work(
    work_data: StudentWorkCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Crea un nuevo trabajo de estudiante.
    Solo el profesor dueño del ciclo escolar puede crear trabajos.
    """
    # Verificar que el estudiante existe
    student = db.query(Student).filter(Student.id == work_data.student_id).first()
    if not student:
        raise NotFoundError("Estudiante", str(work_data.student_id))
    
    # Verificar que el campo formativo existe
    formative_field = db.query(FormativeField).filter(
        FormativeField.id == work_data.formative_field_id
    ).first()
    if not formative_field:
        raise NotFoundError("Campo formativo", str(work_data.formative_field_id))
    
    # Verificar que el parcial existe
    partial = db.query(Partial).filter(
        Partial.id == work_data.partial_id
    ).first()
    if not partial:
        raise NotFoundError("Parcial", str(work_data.partial_id))
    
    # Verificar que el tipo de trabajo existe
    work_type = db.query(WorkType).filter(
        WorkType.id == work_data.work_type_id
    ).first()
    if not work_type:
        raise NotFoundError("Tipo de trabajo", str(work_data.work_type_id))
    
    # Verificar que todos pertenecen al mismo ciclo escolar
    if (student.school_cycle_id != formative_field.school_cycle_id or 
        formative_field.school_cycle_id != partial.school_cycle_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estudiante, campo formativo y parcial deben pertenecer al mismo ciclo escolar."
        )
    
    # Obtener el ciclo escolar
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == student.school_cycle_id
    ).first()
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para crear trabajos en este ciclo escolar. Solo el profesor dueño del ciclo puede crear trabajos."
        )
    
    # Crear el trabajo
    new_work = StudentWork(
        student_id=work_data.student_id,
        formative_field_id=work_data.formative_field_id,
        partial_id=work_data.partial_id,
        work_type_id=work_data.work_type_id,
        teacher_id=current_user.id,
        name=work_data.name,
        grade=work_data.grade,
        work_date=work_data.work_date
    )
    
    db.add(new_work)
    db.commit()
    db.refresh(new_work)
    
    work_response = StudentWorkResponse.model_validate(new_work)
    return created_response(data=work_response)


@router.get("/", response_model=GenericResponse[List[StudentWorkResponse]])
async def list_student_works(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    student_id: int = Query(None, description="Filtrar por ID de estudiante"),
    formative_field_id: int = Query(None, description="Filtrar por ID de campo formativo"),
    partial_id: int = Query(None, description="Filtrar por ID de parcial"),
    work_type_id: int = Query(None, description="Filtrar por ID de tipo de trabajo"),
    school_cycle_id: int = Query(None, description="Filtrar por ID de ciclo escolar"),
    teacher_id: int = Query(None, description="Filtrar por ID de profesor")
):
    """
    Lista todos los trabajos de estudiantes con filtros y paginación.
    """
    query = db.query(StudentWork)
    
    # Si se especifica teacher_id, filtrar por profesor
    if teacher_id:
        query = query.filter(StudentWork.teacher_id == teacher_id)
    
    # Si se especifica school_cycle_id, filtrar por ciclo
    if school_cycle_id:
        query = query.join(Student).filter(Student.school_cycle_id == school_cycle_id)
    
    # Si se especifica student_id, filtrar por estudiante
    if student_id:
        query = query.filter(StudentWork.student_id == student_id)
    
    # Si se especifica formative_field_id, filtrar por campo formativo
    if formative_field_id:
        query = query.filter(StudentWork.formative_field_id == formative_field_id)
    
    # Si se especifica partial_id, filtrar por parcial
    if partial_id:
        query = query.filter(StudentWork.partial_id == partial_id)
    
    # Si se especifica work_type_id, filtrar por tipo de trabajo
    if work_type_id:
        query = query.filter(StudentWork.work_type_id == work_type_id)
    
    works = query.offset(skip).limit(limit).all()
    works_list = [StudentWorkResponse.model_validate(work) for work in works]
    return success_response(data=works_list)


@router.get("/{work_id}", response_model=GenericResponse[StudentWorkResponse])
async def get_student_work(
    work_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene un trabajo de estudiante por ID.
    """
    work = db.query(StudentWork).filter(StudentWork.id == work_id).first()
    
    if not work:
        raise NotFoundError("Trabajo de estudiante", str(work_id))
    
    work_response = StudentWorkResponse.model_validate(work)
    return success_response(data=work_response)


@router.put("/{work_id}", response_model=GenericResponse[StudentWorkResponse])
async def update_student_work(
    work_id: int,
    work_data: StudentWorkUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Actualiza un trabajo de estudiante.
    Solo el profesor dueño del ciclo escolar puede actualizar trabajos.
    """
    work = db.query(StudentWork).filter(StudentWork.id == work_id).first()
    
    if not work:
        raise NotFoundError("Trabajo de estudiante", str(work_id))
    
    # Obtener el estudiante para verificar el ciclo escolar
    student = db.query(Student).filter(Student.id == work.student_id).first()
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == student.school_cycle_id
    ).first()
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este trabajo. Solo el profesor dueño del ciclo puede actualizar trabajos."
        )
    
    # Validar IDs si se están cambiando
    update_data = work_data.model_dump(exclude_unset=True)
    
    if "student_id" in update_data:
        new_student = db.query(Student).filter(Student.id == update_data["student_id"]).first()
        if not new_student:
            raise NotFoundError("Estudiante", str(update_data["student_id"]))
    
    if "formative_field_id" in update_data:
        new_field = db.query(FormativeField).filter(
            FormativeField.id == update_data["formative_field_id"]
        ).first()
        if not new_field:
            raise NotFoundError("Campo formativo", str(update_data["formative_field_id"]))
    
    if "partial_id" in update_data:
        new_partial = db.query(Partial).filter(Partial.id == update_data["partial_id"]).first()
        if not new_partial:
            raise NotFoundError("Parcial", str(update_data["partial_id"]))
    
    if "work_type_id" in update_data:
        new_work_type = db.query(WorkType).filter(WorkType.id == update_data["work_type_id"]).first()
        if not new_work_type:
            raise NotFoundError("Tipo de trabajo", str(update_data["work_type_id"]))
    
    # Actualizar los campos
    for field_key, value in update_data.items():
        setattr(work, field_key, value)
    
    db.commit()
    db.refresh(work)
    
    work_response = StudentWorkResponse.model_validate(work)
    return success_response(data=work_response)


@router.delete("/{work_id}", response_model=GenericResponse[None])
async def delete_student_work(
    work_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Elimina un trabajo de estudiante.
    Solo el profesor dueño del ciclo escolar puede eliminar trabajos.
    """
    work = db.query(StudentWork).filter(StudentWork.id == work_id).first()
    
    if not work:
        raise NotFoundError("Trabajo de estudiante", str(work_id))
    
    # Obtener el estudiante para verificar el ciclo escolar
    student = db.query(Student).filter(Student.id == work.student_id).first()
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == student.school_cycle_id
    ).first()
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este trabajo. Solo el profesor dueño del ciclo puede eliminar trabajos."
        )
    
    db.delete(work)
    db.commit()
    
    return success_response(data=None)

