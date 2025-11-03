"""
Modelo para trabajos/evaluaciones de estudiantes.
"""
from sqlalchemy import Column, BigInteger, String, DECIMAL, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class StudentWork(Base):
    """Modelo para trabajos de estudiantes."""
    __tablename__ = "student_works"
    
    id = Column(BigInteger, primary_key=True, index=True)
    student_id = Column(BigInteger, ForeignKey("students.id"), nullable=False, index=True)
    formative_field_id = Column(BigInteger, ForeignKey("formative_fields.id"), nullable=False, index=True)
    partial_id = Column(BigInteger, ForeignKey("partials.id"), nullable=False, index=True)
    work_type_id = Column(BigInteger, ForeignKey("work_types.id"), nullable=False, index=True)
    teacher_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    grade = Column(DECIMAL(5, 2), nullable=True)
    work_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    student = relationship("Student", back_populates="student_works")
    formative_field = relationship("FormativeField", back_populates="student_works")
    partial = relationship("Partial", back_populates="student_works")
    work_type = relationship("WorkType", back_populates="student_works")
    teacher = relationship("User", back_populates="student_works")
    
    def __repr__(self):
        return f"<StudentWork(id={self.id}, student_id={self.student_id}, name='{self.name}', grade={self.grade})>"

