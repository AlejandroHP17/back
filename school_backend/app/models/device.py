"""
Modelo para dispositivos móviles (IMEI) asociados a usuarios.
"""
from sqlalchemy import Column, BigInteger, String, Boolean, DECIMAL, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class Device(Base):
    """Modelo para dispositivos móviles asociados a usuarios."""
    __tablename__ = "devices"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    imei = Column(String(500), nullable=False, index=True)  # Identificador único del dispositivo (Build.FINGERPRINT + Build.ID)
    latitude = Column(DECIMAL(10, 6), nullable=True)  # Última latitud conocida
    longitude = Column(DECIMAL(10, 6), nullable=True)  # Última longitud conocida
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime, nullable=True)  # Último login exitoso
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relaciones
    user = relationship("User", back_populates="devices")
    
    # Índice único para evitar duplicados de IMEI por usuario
    __table_args__ = (
        Index('idx_user_imei', 'user_id', 'imei', unique=True),
    )
    
    def __repr__(self):
        return f"<Device(id={self.id}, user_id={self.user_id}, imei='{self.imei}', is_active={self.is_active})>"

