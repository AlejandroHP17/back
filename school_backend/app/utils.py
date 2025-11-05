"""
Utilidades y funciones auxiliares reutilizables.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.cycle import SchoolCycle
from app.models.partial import Partial
from app.models.formative_field import FormativeField
from app.models.student import Student
from app.models.user import User
from app.exceptions import NotFoundError, HTTPException
from fastapi import status


def verify_same_school_cycle(
    db: Session,
    formative_field_id: Optional[int] = None,
    partial_id: Optional[int] = None,
    student_id: Optional[int] = None,
    error_detail: str = "Los recursos deben pertenecer al mismo ciclo escolar."
) -> int:
    """
    Verifica que los recursos proporcionados pertenezcan al mismo ciclo escolar.
    
    Args:
        db: Sesión de base de datos
        formative_field_id: ID del campo formativo (opcional)
        partial_id: ID del parcial (opcional)
        student_id: ID del estudiante (opcional)
        error_detail: Mensaje de error personalizado
        
    Returns:
        int: ID del ciclo escolar común
        
    Raises:
        NotFoundError: Si algún recurso no existe
        HTTPException: Si los recursos no pertenecen al mismo ciclo escolar
    """
    cycle_ids = []
    
    if formative_field_id:
        field = db.query(FormativeField).filter(FormativeField.id == formative_field_id).first()
        if not field:
            raise NotFoundError("Campo formativo", str(formative_field_id))
        cycle_ids.append(field.school_cycle_id)
    
    if partial_id:
        partial = db.query(Partial).filter(Partial.id == partial_id).first()
        if not partial:
            raise NotFoundError("Parcial", str(partial_id))
        cycle_ids.append(partial.school_cycle_id)
    
    if student_id:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise NotFoundError("Estudiante", str(student_id))
        cycle_ids.append(student.school_cycle_id)
    
    if not cycle_ids:
        raise ValueError("Debe proporcionarse al menos un ID para verificar el ciclo escolar")
    
    # Verificar que todos pertenecen al mismo ciclo
    if len(set(cycle_ids)) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )
    
    return cycle_ids[0]


def verify_cycle_ownership(
    db: Session,
    school_cycle_id: int,
    current_user: User,
    error_detail: str = "No tienes permiso para realizar esta acción. Solo el profesor dueño del ciclo puede realizarla."
) -> SchoolCycle:
    """
    Verifica que el usuario actual es el profesor dueño del ciclo escolar.
    
    Args:
        db: Sesión de base de datos
        school_cycle_id: ID del ciclo escolar
        current_user: Usuario actual
        error_detail: Mensaje de error personalizado
        
    Returns:
        SchoolCycle: Objeto del ciclo escolar
        
    Raises:
        NotFoundError: Si el ciclo escolar no existe
        HTTPException: Si el usuario no es el profesor del ciclo
    """
    school_cycle = db.query(SchoolCycle).filter(SchoolCycle.id == school_cycle_id).first()
    if not school_cycle:
        raise NotFoundError("Ciclo escolar", str(school_cycle_id))
    
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_detail
        )
    
    return school_cycle

