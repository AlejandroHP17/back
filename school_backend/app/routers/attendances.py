"""
Router para gestión de asistencias.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from app.database import get_db
from app.models.attendance import Attendance
from app.models.student import Student
from app.models.cycle import SchoolCycle
from app.models.partial import Partial
from app.models.user import User
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceResponse
)
from app.dependencies import get_current_active_user
from app.exceptions import NotFoundError, ConflictError

router = APIRouter(
    prefix="/attendances",
    tags=["asistencias"]
)


@router.post("/", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def create_attendance(
    attendance_data: AttendanceCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Crea un nuevo registro de asistencia.
    Solo el profesor dueño del ciclo escolar puede crear asistencias.
    """
    # Verificar que el estudiante existe
    student = db.query(Student).filter(Student.id == attendance_data.student_id).first()
    if not student:
        raise NotFoundError("Estudiante", str(attendance_data.student_id))
    
    # Verificar que el parcial existe
    partial = db.query(Partial).filter(Partial.id == attendance_data.partial_id).first()
    if not partial:
        raise NotFoundError("Parcial", str(attendance_data.partial_id))
    
    # Verificar que el ciclo escolar existe
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == attendance_data.school_cycle_id
    ).first()
    if not school_cycle:
        raise NotFoundError("Ciclo escolar", str(attendance_data.school_cycle_id))
    
    # Verificar que el estudiante pertenece al ciclo escolar especificado
    if student.school_cycle_id != attendance_data.school_cycle_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estudiante no pertenece al ciclo escolar especificado."
        )
    
    # Verificar que el parcial pertenece al mismo ciclo escolar
    if partial.school_cycle_id != attendance_data.school_cycle_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parcial no pertenece al ciclo escolar especificado."
        )
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para crear asistencias en este ciclo escolar. Solo el profesor dueño del ciclo puede crear asistencias."
        )
    
    # Verificar que no existe ya una asistencia para este estudiante en esta fecha
    existing_attendance = db.query(Attendance).filter(
        and_(
            Attendance.student_id == attendance_data.student_id,
            Attendance.attendance_date == attendance_data.attendance_date,
            Attendance.school_cycle_id == attendance_data.school_cycle_id
        )
    ).first()
    
    if existing_attendance:
        raise ConflictError(f"Ya existe un registro de asistencia para este estudiante en la fecha {attendance_data.attendance_date}")
    
    # Crear la asistencia
    new_attendance = Attendance(
        student_id=attendance_data.student_id,
        partial_id=attendance_data.partial_id,
        school_cycle_id=attendance_data.school_cycle_id,
        attendance_date=attendance_data.attendance_date,
        status=attendance_data.status
    )
    
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    
    return AttendanceResponse.model_validate(new_attendance)


@router.get("/", response_model=List[AttendanceResponse])
async def list_attendances(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    student_id: int = Query(None, description="Filtrar por ID de estudiante"),
    partial_id: int = Query(None, description="Filtrar por ID de parcial"),
    school_cycle_id: int = Query(None, description="Filtrar por ID de ciclo escolar"),
    teacher_id: int = Query(None, description="Filtrar por ID de profesor (solo ciclos del profesor)"),
    attendance_date: date = Query(None, description="Filtrar por fecha de asistencia"),
    status: str = Query(None, description="Filtrar por estado (present, absent, late)")
):
    """
    Lista todos los registros de asistencia con filtros y paginación.
    Si se especifica teacher_id, solo muestra asistencias de ciclos pertenecientes a ese profesor.
    """
    query = db.query(Attendance)
    
    # Si se especifica teacher_id, filtrar por ciclos del profesor
    if teacher_id:
        query = query.join(SchoolCycle).filter(SchoolCycle.teacher_id == teacher_id)
    
    # Si se especifica school_cycle_id, filtrar por ciclo
    if school_cycle_id:
        query = query.filter(Attendance.school_cycle_id == school_cycle_id)
    
    # Si se especifica student_id, filtrar por estudiante
    if student_id:
        query = query.filter(Attendance.student_id == student_id)
    
    # Si se especifica partial_id, filtrar por parcial
    if partial_id:
        query = query.filter(Attendance.partial_id == partial_id)
    
    # Si se especifica attendance_date, filtrar por fecha
    if attendance_date:
        query = query.filter(Attendance.attendance_date == attendance_date)
    
    # Si se especifica status, filtrar por estado
    if status:
        query = query.filter(Attendance.status == status)
    
    attendances = query.offset(skip).limit(limit).all()
    return [AttendanceResponse.model_validate(attendance) for attendance in attendances]


@router.get("/{attendance_id}", response_model=AttendanceResponse)
async def get_attendance(
    attendance_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene un registro de asistencia por ID.
    """
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    
    if not attendance:
        raise NotFoundError("Asistencia", str(attendance_id))
    
    return AttendanceResponse.model_validate(attendance)


@router.put("/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: int,
    attendance_data: AttendanceUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Actualiza un registro de asistencia.
    Solo el profesor dueño del ciclo escolar puede actualizar asistencias.
    """
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    
    if not attendance:
        raise NotFoundError("Asistencia", str(attendance_id))
    
    # Obtener el ciclo escolar asociado
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == attendance.school_cycle_id
    ).first()
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar esta asistencia. Solo el profesor dueño del ciclo puede actualizar asistencias."
        )
    
    # Si se está cambiando algún ID, validar
    update_data = attendance_data.model_dump(exclude_unset=True)
    
    # Validar estudiante si se está cambiando
    if "student_id" in update_data and update_data["student_id"] != attendance.student_id:
        new_student = db.query(Student).filter(Student.id == update_data["student_id"]).first()
        if not new_student:
            raise NotFoundError("Estudiante", str(update_data["student_id"]))
        
        # Verificar que el nuevo estudiante pertenece al ciclo escolar
        school_cycle_id = update_data.get("school_cycle_id", attendance.school_cycle_id)
        if new_student.school_cycle_id != school_cycle_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El estudiante no pertenece al ciclo escolar especificado."
            )
    
    # Validar parcial si se está cambiando
    if "partial_id" in update_data and update_data["partial_id"] != attendance.partial_id:
        new_partial = db.query(Partial).filter(Partial.id == update_data["partial_id"]).first()
        if not new_partial:
            raise NotFoundError("Parcial", str(update_data["partial_id"]))
        
        # Verificar que el nuevo parcial pertenece al ciclo escolar
        school_cycle_id = update_data.get("school_cycle_id", attendance.school_cycle_id)
        if new_partial.school_cycle_id != school_cycle_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El parcial no pertenece al ciclo escolar especificado."
            )
    
    # Validar ciclo escolar si se está cambiando
    if "school_cycle_id" in update_data and update_data["school_cycle_id"] != attendance.school_cycle_id:
        new_cycle = db.query(SchoolCycle).filter(
            SchoolCycle.id == update_data["school_cycle_id"]
        ).first()
        if not new_cycle:
            raise NotFoundError("Ciclo escolar", str(update_data["school_cycle_id"]))
        
        if new_cycle.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para mover esta asistencia a ese ciclo escolar."
            )
        
        # Verificar que el estudiante y parcial pertenecen al nuevo ciclo
        student_id = update_data.get("student_id", attendance.student_id)
        partial_id = update_data.get("partial_id", attendance.partial_id)
        
        student = db.query(Student).filter(Student.id == student_id).first()
        partial = db.query(Partial).filter(Partial.id == partial_id).first()
        
        if student.school_cycle_id != update_data["school_cycle_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El estudiante no pertenece al ciclo escolar especificado."
            )
        
        if partial.school_cycle_id != update_data["school_cycle_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El parcial no pertenece al ciclo escolar especificado."
            )
    
    # Verificar duplicados si se está cambiando fecha o estudiante
    if "attendance_date" in update_data or "student_id" in update_data or "school_cycle_id" in update_data:
        new_student_id = update_data.get("student_id", attendance.student_id)
        new_date = update_data.get("attendance_date", attendance.attendance_date)
        new_cycle_id = update_data.get("school_cycle_id", attendance.school_cycle_id)
        
        existing_attendance = db.query(Attendance).filter(
            and_(
                Attendance.student_id == new_student_id,
                Attendance.attendance_date == new_date,
                Attendance.school_cycle_id == new_cycle_id,
                Attendance.id != attendance_id
            )
        ).first()
        
        if existing_attendance:
            raise ConflictError(f"Ya existe un registro de asistencia para este estudiante en la fecha {new_date}")
    
    # Actualizar los campos
    for field_key, value in update_data.items():
        setattr(attendance, field_key, value)
    
    db.commit()
    db.refresh(attendance)
    
    return AttendanceResponse.model_validate(attendance)


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(
    attendance_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Elimina un registro de asistencia.
    Solo el profesor dueño del ciclo escolar puede eliminar asistencias.
    """
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    
    if not attendance:
        raise NotFoundError("Asistencia", str(attendance_id))
    
    # Obtener el ciclo escolar asociado
    school_cycle = db.query(SchoolCycle).filter(
        SchoolCycle.id == attendance.school_cycle_id
    ).first()
    
    # Verificar que el usuario es el profesor del ciclo escolar
    if school_cycle.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar esta asistencia. Solo el profesor dueño del ciclo puede eliminar asistencias."
        )
    
    db.delete(attendance)
    db.commit()
    
    return None

