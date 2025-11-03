"""
Modelo para asistencias.
"""
from sqlalchemy import Column, BigInteger, Boolean, String, Date, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class Attendance(Base):
    """Modelo para asistencias."""
    __tablename__ = "attendances"
    
    id = Column(BigInteger, primary_key=True, index=True)
    student_id = Column(BigInteger, ForeignKey("students.id"), nullable=False, index=True)
    partial_id = Column(BigInteger, ForeignKey("partials.id"), nullable=False, index=True)
    attendance_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default='present')  # present, absent, late
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    student = relationship("Student", back_populates="attendances")
    partial = relationship("Partial", back_populates="attendances")
    
    def __repr__(self):
        return f"<Attendance(id={self.id}, student_id={self.student_id}, partial_id={self.partial_id}, attendance_date={self.attendance_date}, status={self.status})>"

