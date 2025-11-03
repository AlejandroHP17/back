"""
Modelo base para todos los modelos SQLAlchemy.
"""
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declared_attr
from app.database import Base as BaseModel


class TimestampMixin:
    """Mixin para agregar timestamps automáticos a los modelos."""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False
        )


class Base(BaseModel):
    """Clase base abstracta para todos los modelos."""
    __abstract__ = True

