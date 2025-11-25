"""
Router para gestión de estudiantes.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.database import get_db
from app.models.student import Student
from app.models.user import User
from app.models.catalog import School
from app.schemas.student import (
    StudentCreate, StudentUpdate, StudentResponse, StudentCreateResponse
)
from app.schemas.response import GenericResponse, success_response, created_response
from app.dependencies import get_current_active_user
from app.exceptions import NotFoundError, ConflictError

router = APIRouter(
    prefix="/students",
    tags=["students"]
)


@router.post("/", response_model=GenericResponse[StudentCreateResponse], status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Crea un nuevo estudiante.
    El teacher_id se establece automáticamente al profesor autenticado.
    """
    # Verificar CURP único si se proporciona
    if student_data.curp:
        existing_student = db.query(Student).filter(Student.curp == student_data.curp).first()
        if existing_student:
            raise ConflictError(f"El CURP {student_data.curp} ya está registrado")
    
    # Crear el estudiante con el teacher_id del usuario autenticado
    student_dict = student_data.model_dump(exclude={"is_active"})  # Excluir is_active para usar el default de la BD
    student_dict["teacher_id"] = current_user.id
    
    new_student = Student(**student_dict)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    student_response = StudentCreateResponse.model_validate(new_student)
    return created_response(data=student_response)


@router.get("/", response_model=GenericResponse[List[StudentResponse]])
async def list_students(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None, description="Buscar por nombre, apellidos o CURP"),
    school_cycle_id: int = Query(None, description="Filtrar por ciclo escolar (opcional)")
):
    """
    Lista los estudiantes del profesor autenticado con paginación y búsqueda.
    Solo muestra los estudiantes donde el profesor autenticado es el teacher_id.
    Opcionalmente se puede filtrar por ciclo escolar.
    """
    # Filtrar por el profesor autenticado
    query = db.query(Student).filter(Student.teacher_id == current_user.id)
    
    # Filtro opcional por ciclo escolar
    if school_cycle_id is not None:
        query = query.filter(Student.school_cycle_id == school_cycle_id)
    
    # Filtro opcional de búsqueda por texto
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Student.first_name.like(search_pattern),
                Student.last_name.like(search_pattern),
                Student.second_last_name.like(search_pattern),
                Student.curp.like(search_pattern)
            )
        )
    
    # Cargar relaciones necesarias
    students = query.options(
        joinedload(Student.school_cycle)
    ).offset(skip).limit(limit).all()
    
    # Construir respuestas con nombres
    students_list = []
    for student in students:
        school = student.school_cycle.school if student.school_cycle and student.school_cycle.school else None
        
        student_dict = {
            "id": student.id,
            "curp": student.curp,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "second_last_name": student.second_last_name,
            "birth_date": student.birth_date,
            "phone": student.phone,
            "teacher_id": student.teacher_id,
            "school_cycle_id": student.school_cycle_id,
            "is_active": student.is_active,
            "created_at": student.created_at,
            "school_cycle_name": student.school_cycle.name if student.school_cycle else None,
            "school_name": school.name if school else None
        }
        students_list.append(StudentResponse.model_validate(student_dict))
    
    return success_response(data=students_list)


@router.get("/{student_id}", response_model=GenericResponse[StudentResponse])
async def get_student(
    student_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene un estudiante por ID.
    Solo permite acceder a estudiantes del profesor autenticado.
    """
    student = db.query(Student).options(
        joinedload(Student.school_cycle)
    ).filter(
        Student.id == student_id,
        Student.teacher_id == current_user.id
    ).first()
    if not student:
        raise NotFoundError("Estudiante", str(student_id))
    
    school = student.school_cycle.school if student.school_cycle and student.school_cycle.school else None
    
    student_dict = {
        "id": student.id,
        "curp": student.curp,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "second_last_name": student.second_last_name,
        "birth_date": student.birth_date,
        "phone": student.phone,
        "teacher_id": student.teacher_id,
        "school_cycle_id": student.school_cycle_id,
        "is_active": student.is_active,
        "created_at": student.created_at,
        "school_cycle_name": student.school_cycle.name if student.school_cycle else None,
        "school_name": school.name if school else None
    }
    student_response = StudentResponse.model_validate(student_dict)
    return success_response(data=student_response)


@router.put("/{student_id}", response_model=GenericResponse[StudentResponse])
async def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Actualiza un estudiante.
    Solo permite actualizar estudiantes del profesor autenticado.
    """
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.teacher_id == current_user.id
    ).first()
    if not student:
        raise NotFoundError("Estudiante", str(student_id))
    
    # Verificar CURP único si se está actualizando
    update_data = student_data.model_dump(exclude_unset=True)
    if "curp" in update_data and update_data["curp"] and update_data["curp"] != student.curp:
        existing_student = db.query(Student).filter(Student.curp == update_data["curp"]).first()
        # Solo lanzar error si el CURP existe y pertenece a OTRO estudiante (no al que se está actualizando)
        if existing_student and existing_student.id != student.id:
            raise ConflictError(f"El CURP {update_data['curp']} ya está registrado por otro estudiante")
    
    for field, value in update_data.items():
        setattr(student, field, value)
    
    db.commit()
    db.refresh(student)
    
    # Recargar con relaciones
    student = db.query(Student).options(
        joinedload(Student.school_cycle)
    ).filter(Student.id == student_id).first()
    
    school = student.school_cycle.school if student.school_cycle and student.school_cycle.school else None
    
    student_dict = {
        "id": student.id,
        "curp": student.curp,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "second_last_name": student.second_last_name,
        "birth_date": student.birth_date,
        "phone": student.phone,
        "teacher_id": student.teacher_id,
        "school_cycle_id": student.school_cycle_id,
        "is_active": student.is_active,
        "created_at": student.created_at,
        "school_cycle_name": student.school_cycle.name if student.school_cycle else None,
        "school_name": school.name if school else None
    }
    student_response = StudentResponse.model_validate(student_dict)
    return success_response(data=student_response)


@router.delete("/{student_id}", response_model=GenericResponse[str])
async def delete_student(
    student_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Elimina un estudiante.
    Solo permite eliminar estudiantes del profesor autenticado.
    """
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.teacher_id == current_user.id
    ).first()
    if not student:
        raise NotFoundError("Estudiante", str(student_id))
    
    db.delete(student)
    db.commit()
    
    return success_response(data="El elemento se ha borrado correctamente")



