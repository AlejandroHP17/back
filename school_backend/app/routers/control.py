"""
Router para registros de administración.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.database import get_db
from app.models.user import User, AccessCode
from app.models.catalog import AccessLevel
from app.schemas.user import AccessCodeCreate, AccessCodeUpdate, AccessCodeResponse
from app.schemas.response import GenericResponse, success_response, created_response
from app.dependencies import get_current_active_user, require_access_level
from app.exceptions import NotFoundError, ConflictError
from app.security import cleanup_expired_refresh_tokens
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/control",
    tags=["administration"]
)


@router.post("/access-codes", response_model=GenericResponse[AccessCodeResponse], status_code=status.HTTP_201_CREATED)
async def create_access_code(
    code_data: AccessCodeCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_access_level("Administrador"))]
):
    """
    Crea un nuevo código de acceso.
    Requiere nivel de acceso: Administrador
    """
    # Verificar si el código ya existe
    existing_code = db.query(AccessCode).filter(AccessCode.code == code_data.code).first()
    if existing_code:
        raise ConflictError(f"El código '{code_data.code}' ya existe")
    
    # Verificar que el access_level_id existe
    access_level = db.query(AccessLevel).filter(AccessLevel.id == code_data.access_level_id).first()
    if not access_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El nivel de acceso con ID {code_data.access_level_id} no existe."
        )
    
    try:
        # Crear nuevo código de acceso
        new_code = AccessCode(
            code=code_data.code,
            access_level_id=code_data.access_level_id,
            description=code_data.description,
            is_active=True,
            created_by=current_user.id
        )
        
        db.add(new_code)
        db.commit()
        db.refresh(new_code)
        
        code_response = AccessCodeResponse.model_validate(new_code)
        return created_response(data=code_response)
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        logger.error(f"Error de integridad al crear código de acceso: {error_msg}")
        
        if "FOREIGN KEY constraint" in error_msg or "Cannot add or update a child row" in error_msg:
            if "access_level_id" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El nivel de acceso especificado no existe."
                )
            elif "created_by" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El usuario creador no existe."
                )
        elif "Duplicate entry" in error_msg or "UNIQUE constraint" in error_msg:
            raise ConflictError(f"El código '{code_data.code}' ya existe")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de integridad: {error_msg}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error de base de datos al crear código de acceso: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de base de datos: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado al crear código de acceso: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )


@router.put("/access-codes/{code_id}", response_model=GenericResponse[AccessCodeResponse])
async def update_access_code_status(
    code_id: int,
    code_update: AccessCodeUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_access_level("Administrador"))]
):
    """
    Actualiza el estado activo/inactivo de un código de acceso.
    Requiere nivel de acceso: Administrador, admin o super_admin
    """
    access_code = db.query(AccessCode).filter(AccessCode.id == code_id).first()
    if not access_code:
        raise NotFoundError("Código de acceso", str(code_id))
    
    # Actualizar solo el estado
    access_code.is_active = code_update.is_active
    
    db.commit()
    db.refresh(access_code)
    
    code_response = AccessCodeResponse.model_validate(access_code)
    return success_response(data=code_response)


@router.get("/access-codes", response_model=GenericResponse[List[AccessCodeResponse]])
async def list_access_codes(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_access_level("Administrador"))],
    active_only: bool = False
):
    """
    Lista todos los códigos de acceso.
    Requiere nivel de acceso: Administrador
    """
    query = db.query(AccessCode)
    
    if active_only:
        query = query.filter(AccessCode.is_active == True)
    
    codes = query.order_by(AccessCode.created_at.desc()).all()
    codes_list = [AccessCodeResponse.model_validate(code) for code in codes]
    return success_response(data=codes_list)


@router.get("/access-codes/{code_id}", response_model=GenericResponse[AccessCodeResponse])
async def get_access_code(
    code_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_access_level("Administrador"))]
):
    """
    Obtiene un código de acceso por ID.
    Requiere nivel de acceso: Administrador
    """
    access_code = db.query(AccessCode).filter(AccessCode.id == code_id).first()
    if not access_code:
        raise NotFoundError("Código de acceso", str(code_id))
    
    code_response = AccessCodeResponse.model_validate(access_code)
    return success_response(data=code_response)


@router.post("/cleanup-tokens", response_model=GenericResponse[dict])
async def cleanup_expired_tokens_manual(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_access_level("Administrador"))]
):
    """
    Ejecuta manualmente la limpieza de refresh tokens expirados.
    Requiere nivel de acceso: Administrador
    
    Esta función elimina todos los refresh tokens que:
    - Han expirado (expires_at < ahora)
    - Están marcados como inactivos (is_active = False)
    """
    try:
        deleted_count = cleanup_expired_refresh_tokens(db)
        logger.info(f"Limpieza manual ejecutada por usuario {current_user.id}: Se eliminaron {deleted_count} tokens")
        
        return success_response(data={
            "deleted_count": deleted_count,
            "message": f"Se eliminaron {deleted_count} refresh tokens expirados o inactivos"
        })
    except Exception as e:
        logger.error(f"Error en limpieza manual de tokens: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar la limpieza: {str(e)}"
        )