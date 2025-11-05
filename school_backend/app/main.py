"""
Aplicación principal FastAPI del sistema escolar.
"""
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.config import settings
from app.routers import auth, schools, students, cycles, control, partials, formative_fields, work_type_evaluations, attendances

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend del Sistema Escolar con FastAPI",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api")
app.include_router(schools.router, prefix="/api")
app.include_router(students.router, prefix="/api")
app.include_router(cycles.router, prefix="/api")
app.include_router(partials.router, prefix="/api")
app.include_router(formative_fields.router, prefix="/api")
app.include_router(work_type_evaluations.router, prefix="/api")
app.include_router(attendances.router, prefix="/api")
app.include_router(control.router, prefix="/api")


@app.get("/", tags=["inicio"])
async def root():
    """Endpoint raíz de la API."""
    return {
        "message": "Bienvenido al Sistema Escolar Backend",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["salud"])
async def health_check():
    """Endpoint de salud para verificar el estado de la API."""
    return {"status": "healthy", "version": settings.APP_VERSION}


# Handler global de excepciones
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Maneja errores de validación de Pydantic."""
    logger.error(f"Error de validación: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body}
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Maneja errores de integridad de base de datos."""
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    logger.error(f"Error de integridad: {error_msg}")
    
    # Mensajes más específicos según el tipo de error
    detail = "Error de integridad: El recurso ya existe o viola restricciones de la base de datos"
    
    if "FOREIGN KEY constraint" in error_msg or "Cannot add or update a child row" in error_msg:
        if "access_level_id" in error_msg:
            detail = "Error: El nivel de acceso especificado no existe. Por favor, crea primero los catálogos ejecutando: python3 seed_data.py"
        elif "school_id" in error_msg:
            detail = "Error: La escuela especificada no existe. El school_id debe ser null o un ID válido."
        elif "school_type_id" in error_msg:
            detail = "Error: El tipo de escuela especificado no existe. Por favor, crea primero los catálogos."
        else:
            detail = f"Error de integridad referencial: {error_msg}"
    elif "Duplicate entry" in error_msg or "UNIQUE constraint" in error_msg:
        detail = "Error: El recurso ya existe (duplicado). Verifica que no estés creando un registro duplicado."
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": detail}
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """Maneja errores generales de SQLAlchemy."""
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    logger.error(f"Error de SQLAlchemy: {error_msg}", exc_info=True)
    
    # Si el modo DEBUG está activo, mostrar más detalles
    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": f"Error de base de datos: {error_msg}",
                "error_type": type(exc).__name__
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error de base de datos. Por favor, intenta nuevamente."}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Maneja todas las demás excepciones no capturadas."""
    logger.error(f"Error no manejado: {type(exc).__name__}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Error interno del servidor",
            "error_type": type(exc).__name__,
            "message": str(exc) if settings.DEBUG else "Ha ocurrido un error. Contacta al administrador."
        }
    )

