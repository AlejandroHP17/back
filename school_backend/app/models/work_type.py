"""
Modelo para tipos de trabajo (evaluaciones).
"""
from sqlalchemy import Column, BigInteger, String, DECIMAL, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class WorkType(Base):
    """Modelo para tipos de trabajo."""
    __tablename__ = "work_types"
    
    id = Column(BigInteger, primary_key=True, index=True)
    teacher_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    evaluation_weight = Column(DECIMAL(5, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    teacher = relationship("User", back_populates="work_types")
    student_works = relationship("StudentWork", back_populates="work_type")
    
    # Restricción única
    __table_args__ = (
        UniqueConstraint("teacher_id", "name", name="uq_worktypes_teacher_name"),
    )
    
    def __repr__(self):
        return f"<WorkType(id={self.id}, teacher_id={self.teacher_id}, name='{self.name}')>"

