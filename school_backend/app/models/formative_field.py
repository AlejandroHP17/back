"""
Modelo para campos formativos (áreas de aprendizaje).
"""
from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class FormativeField(Base):
    """Modelo para campos formativos."""
    __tablename__ = "formative_fields"
    
    id = Column(BigInteger, primary_key=True, index=True)
    school_cycle_id = Column(BigInteger, ForeignKey("school_cycles.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    code = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    school_cycle = relationship("SchoolCycle", back_populates="formative_fields")
    student_works = relationship("StudentWork", back_populates="formative_field")
    work_type_evaluations = relationship("WorkTypeEvaluation", back_populates="formative_field")
    
    def __repr__(self):
        return f"<FormativeField(id={self.id}, school_cycle_id={self.school_cycle_id}, name='{self.name}')>"

