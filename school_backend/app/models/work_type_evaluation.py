"""
Modelo para pesos de evaluación por tipo de trabajo, campo formativo y parcial.
"""
from sqlalchemy import Column, BigInteger, DECIMAL, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class WorkTypeEvaluation(Base):
    """Modelo para pesos de evaluación."""
    __tablename__ = "work_type_evaluations"
    
    id = Column(BigInteger, primary_key=True, index=True)
    formative_field_id = Column(BigInteger, ForeignKey("formative_fields.id"), nullable=False, index=True)
    partial_id = Column(BigInteger, ForeignKey("partials.id"), nullable=False, index=True)
    work_type_id = Column(BigInteger, ForeignKey("work_types.id"), nullable=False, index=True)
    evaluation_weight = Column(DECIMAL(5, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    formative_field = relationship("FormativeField", back_populates="work_type_evaluations")
    partial = relationship("Partial", back_populates="work_type_evaluations")
    work_type = relationship("WorkType", back_populates="work_type_evaluations")
    
    # Restricción única para asegurar que no haya duplicados
    __table_args__ = (
        UniqueConstraint("formative_field_id", "partial_id", "work_type_id", name="uq_work_eval_unique"),
    )
    
    def __repr__(self):
        return f"<WorkTypeEvaluation(id={self.id}, formative_field_id={self.formative_field_id}, partial_id={self.partial_id}, work_type_id={self.work_type_id}, weight={self.evaluation_weight})>"

