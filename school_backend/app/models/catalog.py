"""
Modelos para tablas de catálogos (school_types, shifts, access_levels).
"""
from sqlalchemy import Column, Integer, String, DateTime, Index, BigInteger, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class SchoolType(Base):
    """Modelo para tipos de escuela."""
    __tablename__ = "school_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    schools = relationship("School", back_populates="school_type")
    
    def __repr__(self):
        return f"<SchoolType(id={self.id}, name='{self.name}')>"


class Shift(Base):
    """Modelo para turnos escolares."""
    __tablename__ = "shifts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    schools = relationship("School", back_populates="shift")
    
    def __repr__(self):
        return f"<Shift(id={self.id}, name='{self.name}')>"


class AccessLevel(Base):
    """Modelo para niveles de acceso de usuarios."""
    __tablename__ = "access_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    users = relationship("User", back_populates="access_level")
    access_codes = relationship("AccessCode", back_populates="access_level")
    
    def __repr__(self):
        return f"<AccessLevel(id={self.id}, name='{self.name}')>"


class School(Base):
    """Modelo para escuelas."""
    __tablename__ = "schools"
    
    id = Column(BigInteger, primary_key=True, index=True)
    cct = Column(String(20), nullable=False, unique=True, index=True)
    school_type_id = Column(Integer, ForeignKey("school_types.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    postal_code = Column(String(5), nullable=True)
    latitude = Column(DECIMAL(10, 6), nullable=True)
    longitude = Column(DECIMAL(10, 6), nullable=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    school_type = relationship("SchoolType", back_populates="schools")
    shift = relationship("Shift", back_populates="schools")
    school_cycles = relationship("SchoolCycle", back_populates="school")
    
    def __repr__(self):
        return f"<School(id={self.id}, cct='{self.cct}', name='{self.name}')>"


