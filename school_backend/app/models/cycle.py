"""
Modelo para ciclos escolares.
"""
from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class SchoolCycle(Base):
    """Modelo para ciclos escolares."""
    __tablename__ = "school_cycles"
    
    id = Column(BigInteger, primary_key=True, index=True)
    school_id = Column(BigInteger, ForeignKey("schools.id"), nullable=False, index=True)
    teacher_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(120), nullable=True)
    cycle_label = Column(String(50), nullable=True)
    grade = Column(String(20), nullable=True)
    group_name = Column(String(20), nullable=True)
    period_catalog_id = Column(Integer, ForeignKey("period_catalog.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    school = relationship("School", back_populates="school_cycles")
    teacher = relationship("User", back_populates="school_cycles")
    period_catalog = relationship("PeriodCatalog", back_populates="school_cycles")
    students = relationship("Student", back_populates="school_cycle", cascade="all, delete-orphan")
    partials = relationship("Partial", back_populates="school_cycle", cascade="all, delete-orphan")
    formative_fields = relationship("FormativeField", back_populates="school_cycle", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="school_cycle", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SchoolCycle(id={self.id}, name='{self.name}', cycle_label='{self.cycle_label}')>"

