"""
Modelos para usuarios y códigos de acceso.
"""
from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class User(Base):
    """Modelo para usuarios."""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String(150), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=True)
    access_level_id = Column(Integer, ForeignKey("access_levels.id"), nullable=False, index=True)
    access_code_id = Column(BigInteger, ForeignKey("access_codes.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    access_level = relationship("AccessLevel", back_populates="users")
    access_code = relationship("AccessCode", foreign_keys=[access_code_id], back_populates="users")
    created_access_codes = relationship(
        "AccessCode",
        foreign_keys="AccessCode.created_by",
        back_populates="creator"
    )
    school_cycles = relationship("SchoolCycle", back_populates="teacher")
    work_types = relationship("WorkType", back_populates="teacher")
    student_works = relationship("StudentWork", back_populates="teacher")
    students = relationship("Student", back_populates="teacher")
    
    @property
    def full_name(self) -> str:
        """Retorna el nombre completo del usuario."""
        parts = [self.first_name or "", self.last_name or ""]
        return " ".join(filter(None, parts)) or None
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}')>"


class AccessCode(Base):
    """Modelo para códigos de acceso."""
    __tablename__ = "access_codes"
    
    id = Column(BigInteger, primary_key=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    access_level_id = Column(Integer, ForeignKey("access_levels.id"), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    access_level = relationship("AccessLevel", back_populates="access_codes")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_access_codes")
    users = relationship("User", foreign_keys="User.access_code_id", back_populates="access_code")
    
    def __repr__(self):
        return f"<AccessCode(id={self.id}, code='{self.code}', is_active={self.is_active})>"

