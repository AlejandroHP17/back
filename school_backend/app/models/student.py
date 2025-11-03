"""
Modelos para estudiantes y su relación con ciclos.
"""
from sqlalchemy import Column, BigInteger, String, Date, DateTime, ForeignKey, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class Student(Base):
    """Modelo para estudiantes."""
    __tablename__ = "students"
    
    id = Column(BigInteger, primary_key=True, index=True)
    curp = Column(String(18), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    birth_date = Column(Date, nullable=True)
    phone = Column(String(30), nullable=True)
    teacher_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    school_cycle_id = Column(BigInteger, ForeignKey("school_cycles.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relaciones
    teacher = relationship("User", back_populates="students")
    school_cycle = relationship("SchoolCycle", back_populates="students")
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    student_works = relationship("StudentWork", back_populates="student", cascade="all, delete-orphan")
    
    @property
    def full_name(self) -> str:
        """Retorna el nombre completo del estudiante."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def __repr__(self):
        return f"<Student(id={self.id}, curp='{self.curp}', full_name='{self.full_name}')>"

