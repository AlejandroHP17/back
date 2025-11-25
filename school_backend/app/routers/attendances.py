"""
Router para gestión de asistencias.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from datetime import date
from app.database import get_db
from app.models.attendance import Attendance
from app.models.student import Student
from app.models.cycle import SchoolCycle
from app.models.partial import Partial
from app.models.user import User
from app.models.catalog import School
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceResponse,
    AttendanceCreateResponse,
    AttendanceBulkCreate,
    AttendanceBulkResponse
)
from app.schemas.response import GenericResponse, success_response, created_response
from app.dependencies import get_current_active_user
from app.exceptions import NotFoundError, ConflictError

router = APIRouter(
    prefix="/attendances",
    tags=["attendances"]
)


@router.post("/bulk", response_model=GenericResponse[AttendanceBulkResponse], status_code=status.HTTP_201_CREATED)
async def create_attendances_bulk(
    bulk_data: AttendanceBulkCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Crea registros de asistencia para una lista de estudiantes presentes.
    Los estudiantes que no estén en la lista se marcarán automáticamente como ausentes (absent).
    Usa el ciclo escolar activo y el parcial activo del profesor si no se especifican.
    """
    today = bulk_data.attendance_date
    
    # Determinar el ciclo escolar a usar
    if bulk_data.school_cycle_id:
        school_cycle = db.query(SchoolCycle).filter(
            SchoolCycle.id == bulk_data.school_cycle_id,
            SchoolCycle.teacher_id == current_user.id
        ).first()
        if not school_cycle:
            raise NotFoundError("Ciclo escolar", str(bulk_data.school_cycle_id))
    else:
        # Buscar el ciclo escolar activo del profesor
        school_cycle = db.query(SchoolCycle).filter(
            SchoolCycle.teacher_id == current_user.id,
            SchoolCycle.is_active == True
        ).order_by(SchoolCycle.created_at.desc()).first()
        
        if not school_cycle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró un ciclo escolar activo para este profesor. Por favor, especifica un school_cycle_id o activa un ciclo escolar."
            )
    
    # Determinar el parcial a usar
    if bulk_data.partial_id:
        partial = db.query(Partial).filter(
            Partial.id == bulk_data.partial_id,
            Partial.school_cycle_id == school_cycle.id
        ).first()
        if not partial:
            raise NotFoundError("Parcial", str(bulk_data.partial_id))
    else:
        # Buscar el parcial activo (el que contiene la fecha actual o el más reciente)
        partial = db.query(Partial).filter(
            Partial.school_cycle_id == school_cycle.id
        ).filter(
            or_(
                and_(Partial.start_date <= today, Partial.end_date >= today),  # Fecha dentro del rango
                Partial.start_date.is_(None),  # Parcial sin fecha de inicio
                Partial.end_date.is_(None)  # Parcial sin fecha de fin
            )
        ).order_by(Partial.start_date.desc()).first()
        
        # Si no hay parcial con fecha, tomar el más reciente
        if not partial:
            partial = db.query(Partial).filter(
                Partial.school_cycle_id == school_cycle.id
            ).order_by(Partial.created_at.desc()).first()
        
        if not partial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró un parcial para este ciclo escolar. Por favor, especifica un partial_id o crea un parcial."
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
    
    # Convertir la lista de IDs presentes a un set para búsqueda rápida
    present_student_ids = set(bulk_data.student_ids)
    
    # Validar que todos los IDs de estudiantes presentes existen y pertenecen al ciclo
    for student_id in present_student_ids:
        student = db.query(Student).filter(
            Student.id == student_id,
            Student.school_cycle_id == school_cycle.id
        ).first()
        if not student:
            raise NotFoundError("Estudiante", str(student_id))
    
    created_attendances = []
    updated_attendances = []
    
    # Procesar todos los estudiantes del ciclo
    for student in all_students:
        # Determinar el estado según si está en la lista de presentes
        status = 'present' if student.id in present_student_ids else 'absent'
        
        # Verificar si ya existe una asistencia para este estudiante en esta fecha
        existing_attendance = db.query(Attendance).filter(
            and_(
                Attendance.student_id == student.id,
                Attendance.attendance_date == today,
                Attendance.school_cycle_id == school_cycle.id
            )
        ).first()
        
        if existing_attendance:
            # Actualizar la asistencia existente
            existing_attendance.status = status
            existing_attendance.partial_id = partial.id
            updated_attendances.append(existing_attendance)
        else:
            # Crear nueva asistencia
            new_attendance = Attendance(
                student_id=student.id,
                partial_id=partial.id,
                school_cycle_id=school_cycle.id,
                attendance_date=today,
                status=status
            )
            db.add(new_attendance)
            created_attendances.append(new_attendance)
    
    try:
        db.commit()
        
        # Refrescar los objetos para obtener los IDs generados
        for attendance in created_attendances:
            db.refresh(attendance)
        for attendance in updated_attendances:
            db.refresh(attendance)
        
        # Cargar relaciones para todos los registros (sin school_cycle)
        all_attendance_ids = [att.id for att in created_attendances + updated_attendances]
        attendances_with_relations = db.query(Attendance).options(
            joinedload(Attendance.student),
            joinedload(Attendance.partial)
        ).filter(Attendance.id.in_(all_attendance_ids)).all()
        
        # Crear diccionario de asistencias por ID
        attendances_dict = {att.id: att for att in attendances_with_relations}
        
        # Construir respuestas con nombres (sin school_cycle ni school)
        created_responses = []
        for attendance in created_attendances:
            att_with_relations = attendances_dict.get(attendance.id)
            if att_with_relations:
                attendance_dict = {
                    "id": att_with_relations.id,
                    "student_id": att_with_relations.student_id,
                    "partial_id": att_with_relations.partial_id,
                    "school_cycle_id": att_with_relations.school_cycle_id,
                    "attendance_date": att_with_relations.attendance_date,
                    "status": att_with_relations.status,
                    "created_at": att_with_relations.created_at,
                    "student_name": att_with_relations.student.full_name if att_with_relations.student else None,
                    "partial_name": att_with_relations.partial.name if att_with_relations.partial else None
                }
                created_responses.append(AttendanceCreateResponse.model_validate(attendance_dict))
        
        updated_responses = []
        for attendance in updated_attendances:
            att_with_relations = attendances_dict.get(attendance.id)
            if att_with_relations:
                attendance_dict = {
                    "id": att_with_relations.id,
                    "student_id": att_with_relations.student_id,
                    "partial_id": att_with_relations.partial_id,
                    "school_cycle_id": att_with_relations.school_cycle_id,
                    "attendance_date": att_with_relations.attendance_date,
                    "status": att_with_relations.status,
                    "created_at": att_with_relations.created_at,
                    "student_name": att_with_relations.student.full_name if att_with_relations.student else None,
                    "partial_name": att_with_relations.partial.name if att_with_relations.partial else None
                }
                updated_responses.append(AttendanceCreateResponse.model_validate(attendance_dict))
        
        total_present = len(present_student_ids)
        total_absent = len(all_students) - total_present
        
        bulk_response = AttendanceBulkResponse(
            created=created_responses,
            updated=updated_responses,
            total_present=total_present,
            total_absent=total_absent,
            school_cycle_id=school_cycle.id,
            partial_id=partial.id,
            attendance_date=today
        )
        return created_response(data=bulk_response)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear asistencias: {str(e)}"
        )


@router.post("/", response_model=GenericResponse[AttendanceCreateResponse], status_code=status.HTTP_201_CREATED)
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
    
    # Cargar relaciones para obtener nombres (sin school_cycle ni school)
    attendance = db.query(Attendance).options(
        joinedload(Attendance.student),
        joinedload(Attendance.partial)
    ).filter(Attendance.id == new_attendance.id).first()
    
    attendance_dict = {
        "id": attendance.id,
        "student_id": attendance.student_id,
        "partial_id": attendance.partial_id,
        "school_cycle_id": attendance.school_cycle_id,
        "attendance_date": attendance.attendance_date,
        "status": attendance.status,
        "created_at": attendance.created_at,
        "student_name": attendance.student.full_name if attendance.student else None,
        "partial_name": attendance.partial.name if attendance.partial else None
    }
    attendance_response = AttendanceCreateResponse.model_validate(attendance_dict)
    return created_response(data=attendance_response)


@router.get("/", response_model=GenericResponse[List[AttendanceResponse]])
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
    
    # Cargar relaciones necesarias
    attendances = query.options(
        joinedload(Attendance.student),
        joinedload(Attendance.partial),
        joinedload(Attendance.school_cycle)
    ).offset(skip).limit(limit).all()
    
    # Construir respuestas con nombres
    attendances_list = []
    for attendance in attendances:
        school = attendance.school_cycle.school if attendance.school_cycle and attendance.school_cycle.school else None
        
        attendance_dict = {
            "id": attendance.id,
            "student_id": attendance.student_id,
            "partial_id": attendance.partial_id,
            "school_cycle_id": attendance.school_cycle_id,
            "attendance_date": attendance.attendance_date,
            "status": attendance.status,
            "created_at": attendance.created_at,
            "student_name": attendance.student.full_name if attendance.student else None,
            "partial_name": attendance.partial.name if attendance.partial else None,
            "school_cycle_name": attendance.school_cycle.name if attendance.school_cycle else None,
            "school_name": school.name if school else None
        }
        attendances_list.append(AttendanceResponse.model_validate(attendance_dict))
    
    return success_response(data=attendances_list)


@router.get("/{attendance_id}", response_model=GenericResponse[AttendanceResponse])
async def get_attendance(
    attendance_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene un registro de asistencia por ID.
    """
    attendance = db.query(Attendance).options(
        joinedload(Attendance.student),
        joinedload(Attendance.partial),
        joinedload(Attendance.school_cycle)
    ).filter(Attendance.id == attendance_id).first()
    
    if not attendance:
        raise NotFoundError("Asistencia", str(attendance_id))
    
    school = attendance.school_cycle.school if attendance.school_cycle and attendance.school_cycle.school else None
    
    attendance_dict = {
        "id": attendance.id,
        "student_id": attendance.student_id,
        "partial_id": attendance.partial_id,
        "school_cycle_id": attendance.school_cycle_id,
        "attendance_date": attendance.attendance_date,
        "status": attendance.status,
        "created_at": attendance.created_at,
        "student_name": attendance.student.full_name if attendance.student else None,
        "partial_name": attendance.partial.name if attendance.partial else None,
        "school_cycle_name": attendance.school_cycle.name if attendance.school_cycle else None,
        "school_name": school.name if school else None
    }
    attendance_response = AttendanceResponse.model_validate(attendance_dict)
    return success_response(data=attendance_response)


@router.put("/{attendance_id}", response_model=GenericResponse[AttendanceResponse])
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
    
    # Recargar con relaciones
    attendance = db.query(Attendance).options(
        joinedload(Attendance.student),
        joinedload(Attendance.partial),
        joinedload(Attendance.school_cycle)
    ).filter(Attendance.id == attendance_id).first()
    
    school = attendance.school_cycle.school if attendance.school_cycle and attendance.school_cycle.school else None
    
    attendance_dict = {
        "id": attendance.id,
        "student_id": attendance.student_id,
        "partial_id": attendance.partial_id,
        "school_cycle_id": attendance.school_cycle_id,
        "attendance_date": attendance.attendance_date,
        "status": attendance.status,
        "created_at": attendance.created_at,
        "student_name": attendance.student.full_name if attendance.student else None,
        "partial_name": attendance.partial.name if attendance.partial else None,
        "school_cycle_name": attendance.school_cycle.name if attendance.school_cycle else None,
        "school_name": school.name if school else None
    }
    attendance_response = AttendanceResponse.model_validate(attendance_dict)
    return success_response(data=attendance_response)


@router.delete("/{attendance_id}", response_model=GenericResponse[str])
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
    
    return success_response(data="El elemento se ha borrado correctamente")

