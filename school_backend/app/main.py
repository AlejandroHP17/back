"""
Aplicación principal FastAPI del sistema escolar.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import settings
from app.routers import auth, schools, students, cycles, control, partials, formative_fields, work_types, work_type_evaluations, attendances, student_works
from app.schemas.response import GenericResponse, get_error_message
from app.database import SessionLocal
from app.security import cleanup_expired_refresh_tokens

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Scheduler para tareas programadas
scheduler = BackgroundScheduler()


def run_token_cleanup():
    """
    Ejecuta la limpieza de tokens expirados.
    Esta función se ejecuta periódicamente mediante el scheduler.
    """
    db = SessionLocal()
    try:
        deleted_count = cleanup_expired_refresh_tokens(db)
        if deleted_count > 0:
            logger.info(f"Limpieza automática: Se eliminaron {deleted_count} refresh tokens expirados")
    except Exception as e:
        logger.error(f"Error en la limpieza automática de tokens: {str(e)}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.
    Inicia el scheduler al arrancar y lo detiene al cerrar.
    """
    # Iniciar scheduler al arrancar
    # Ejecutar limpieza todos los días a las 2:00 AM
    scheduler.add_job(
        run_token_cleanup,
        trigger=CronTrigger(hour=2, minute=0),
        id='cleanup_expired_tokens',
        name='Limpieza de tokens expirados',
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler iniciado: Limpieza automática de tokens configurada (diaria a las 2:00 AM)")
    
    yield
    
    # Detener scheduler al cerrar
    scheduler.shutdown()
    logger.info("Scheduler detenido")


# Crear la aplicación FastAPI con lifespan
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend del Sistema Escolar con FastAPI",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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
app.include_router(work_types.router, prefix="/api")
app.include_router(work_type_evaluations.router, prefix="/api")
app.include_router(attendances.router, prefix="/api")
app.include_router(student_works.router, prefix="/api")
app.include_router(control.router, prefix="/api")


@app.get("/", tags=["root"])
async def root():
    """
    Endpoint raíz de la API.
    
    Returns:
        dict: Información básica de la API incluyendo versión y URLs de documentación.
    """
    return {
        "message": "Bienvenido al Sistema Escolar Backend",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Endpoint de salud para verificar el estado de la API.
    
    Returns:
        dict: Estado de la API y versión.
    """
    return {"status": "healthy", "version": settings.APP_VERSION}


# Handler global de excepciones
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Maneja excepciones HTTP y las convierte al formato GenericResponse."""
    error_message = get_error_message(exc.status_code, exc.detail)
    response = GenericResponse(
        data=None,
        response={
            "code": exc.status_code,
            "message": error_message
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode='json')
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Maneja errores de validación de Pydantic."""
    logger.error(f"Error de validación: {exc.errors()}")
    error_message = get_error_message(status.HTTP_422_UNPROCESSABLE_ENTITY, "Los datos proporcionados no son válidos")
    response = GenericResponse(
        data={"errors": exc.errors(), "body": exc.body},
        response={
            "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": error_message
        }
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(mode='json')
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
    
    error_message = get_error_message(status.HTTP_409_CONFLICT, detail)
    response = GenericResponse(
        data=None,
        response={
            "code": status.HTTP_409_CONFLICT,
            "message": error_message
        }
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(mode='json')
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """Maneja errores generales de SQLAlchemy."""
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    logger.error(f"Error de SQLAlchemy: {error_msg}", exc_info=True)
    
    error_message = get_error_message(status.HTTP_500_INTERNAL_SERVER_ERROR)
    response_data = None
    
    # Si el modo DEBUG está activo, mostrar más detalles
    if settings.DEBUG:
        response_data = {
            "error_detail": f"Error de base de datos: {error_msg}",
            "error_type": type(exc).__name__
        }
        error_message = get_error_message(status.HTTP_500_INTERNAL_SERVER_ERROR, error_msg)
    
    response = GenericResponse(
        data=response_data,
        response={
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": error_message
        }
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(mode='json')
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Maneja todas las demás excepciones no capturadas."""
    logger.error(f"Error no manejado: {type(exc).__name__}: {str(exc)}", exc_info=True)
    
    error_message = get_error_message(status.HTTP_500_INTERNAL_SERVER_ERROR)
    response_data = None
    
    if settings.DEBUG:
        # Convertir el error a string de forma segura, manejando bytes
        error_detail = str(exc)
        if isinstance(exc, bytes):
            try:
                error_detail = exc.decode('utf-8')
            except (UnicodeDecodeError, AttributeError):
                error_detail = repr(exc)
        elif hasattr(exc, '__bytes__'):
            try:
                error_detail = bytes(exc).decode('utf-8')
            except (UnicodeDecodeError, AttributeError):
                error_detail = str(exc)
        
        response_data = {
            "error_type": type(exc).__name__,
            "error_detail": error_detail
        }
        error_message = get_error_message(status.HTTP_500_INTERNAL_SERVER_ERROR, error_detail)
    
    response = GenericResponse(
        data=response_data,
        response={
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": error_message
        }
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(mode='json')
    )

