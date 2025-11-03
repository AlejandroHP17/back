"""
Configuración de la base de datos con SQLAlchemy.
Gestiona la conexión y la sesión de base de datos.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import settings

# Crear el motor de base de datos
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
    pool_recycle=3600,   # Recicla conexiones cada hora
    pool_size=10,        # Tamaño del pool de conexiones
    max_overflow=20,     # Conexiones adicionales permitidas
    echo=settings.DEBUG  # Muestra queries SQL en modo debug
)

# Crear la clase base para los modelos
Base = declarative_base()

# Crear el factory de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependencia para obtener la sesión de base de datos.
    Cierra automáticamente la sesión al finalizar.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Configuraciones específicas para MySQL si es necesario."""
    # Puedes agregar configuraciones específicas aquí
    pass

