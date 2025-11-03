"""
Modelo para parciales (períodos de evaluación).
"""
from sqlalchemy import Column, BigInteger, String, Date, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class Partial(Base):
    """Modelo para parciales."""
    __tablename__ = "partials"
    
    id = Column(BigInteger, primary_key=True, index=True)
    school_cycle_id = Column(BigInteger, ForeignKey("school_cycles.id"), nullable=False, index=True)
    name = Column(String(80), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    school_cycle = relationship("SchoolCycle", back_populates="partials")
    attendances = relationship("Attendance", back_populates="partial", cascade="all, delete-orphan")
    student_works = relationship("StudentWork", back_populates="partial")
    
    def __repr__(self):
        return f"<Partial(id={self.id}, school_cycle_id={self.school_cycle_id}, name='{self.name}')>"

