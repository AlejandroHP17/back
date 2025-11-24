"""
Modelo para refresh tokens JWT.
"""
from sqlalchemy import Column, BigInteger, String, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class RefreshToken(Base):
    """Modelo para refresh tokens asociados a usuarios."""
    __tablename__ = "refresh_tokens"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(500), nullable=False, unique=True, index=True)  # El refresh token JWT
    is_active = Column(Boolean, default=True, nullable=False)  # Para invalidar tokens
    expires_at = Column(DateTime, nullable=False, index=True)  # Fecha de expiración
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    user = relationship("User", back_populates="refresh_tokens")
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, is_active={self.is_active}, expires_at={self.expires_at})>"

