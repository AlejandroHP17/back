"""
Router para autenticación y gestión de usuarios.
"""
from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRegister, UserResponse, Token
from app.security import verify_password, get_password_hash, create_access_token
from app.dependencies import get_current_user
from app.exceptions import UnauthorizedError, ConflictError

router = APIRouter(
    prefix="/auth",
    tags=["autenticación"]
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Registra un nuevo usuario en el sistema.
    Requiere: email, password y access_code_id.
    El access_level_id se obtiene automáticamente del código de acceso.
    """
    # Verificar si el email ya existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise ConflictError(f"El email {user_data.email} ya está registrado")
    
    # Verificar que el código de acceso existe y está activo
    from app.models.user import AccessCode
    access_code = db.query(AccessCode).filter(AccessCode.id == user_data.access_code_id).first()
    
    if not access_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El código de acceso con ID {user_data.access_code_id} no existe."
        )
    
    if not access_code.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de acceso no está activo."
        )
    
    if access_code.used_by is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de acceso ya ha sido utilizado."
        )
    
    # Obtener el access_level_id del código
    access_level_id = access_code.access_level_id
    
    # Crear nuevo usuario
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=None,  # Se puede actualizar después
        last_name=None,   # Se puede actualizar después
        phone=None,       # Se puede actualizar después
        access_level_id=access_level_id,
        access_code_id=user_data.access_code_id,
        is_active=True
    )
    
    db.add(new_user)
    db.flush()  # Para obtener el ID del usuario antes del commit
    
    # Marcar el código como usado
    access_code.used_by = new_user.id
    access_code.used_at = datetime.utcnow()
    
    db.commit()
    db.refresh(new_user)
    
    # Limpiar relaciones antes de devolver
    return UserResponse.model_validate(new_user)


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Autentica un usuario y retorna un token JWT.
    """
    # Buscar usuario por email (OAuth2PasswordRequestForm usa 'username')
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        raise UnauthorizedError("Credenciales inválidas")
    
    if not verify_password(form_data.password, user.password_hash):
        raise UnauthorizedError("Credenciales inválidas")
    
    if not user.is_active:
        raise UnauthorizedError("Usuario inactivo")
    
    # Crear token JWT
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "access_level_id": user.access_level_id}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Obtiene la información del usuario autenticado.
    """
    return UserResponse.model_validate(current_user)

