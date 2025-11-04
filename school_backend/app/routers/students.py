"""
Router para gestión de estudiantes.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.student import Student
from app.models.user import User
from app.schemas.student import (
    StudentCreate, StudentUpdate, StudentResponse
)
from app.dependencies import get_current_active_user
from app.exceptions import NotFoundError, ConflictError

router = APIRouter(
    prefix="/students",
    tags=["estudiantes"]
)


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Crea un nuevo estudiante.
    """
    # Verificar CURP único si se proporciona
    if student_data.curp:
        existing_student = db.query(Student).filter(Student.curp == student_data.curp).first()
        if existing_student:
            raise ConflictError(f"El CURP {student_data.curp} ya está registrado")
    
    new_student = Student(**student_data.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    return StudentResponse.model_validate(new_student)


@router.get("/", response_model=List[StudentResponse])
async def list_students(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None, description="Buscar por nombre, apellidos o CURP")
):
    """
    Lista todos los estudiantes con paginación y búsqueda.
    """
    query = db.query(Student)
    
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
    
    students = query.offset(skip).limit(limit).all()
    return [StudentResponse.model_validate(student) for student in students]


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Obtiene un estudiante por ID.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundError("Estudiante", str(student_id))
    
    return StudentResponse.model_validate(student)


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Actualiza un estudiante.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
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
    
    return StudentResponse.model_validate(student)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Elimina un estudiante.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundError("Estudiante", str(student_id))
    
    db.delete(student)
    db.commit()
    
    return None



