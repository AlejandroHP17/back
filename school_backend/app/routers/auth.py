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
from app.models.device import Device
from app.schemas.user import UserCreate, UserRegister, UserResponse, Token, UserLogin
from app.schemas.response import GenericResponse, success_response, created_response
from app.security import verify_password, get_password_hash, create_access_token, validate_imei, validate_coordinates
from app.dependencies import get_current_user
from app.exceptions import UnauthorizedError, ConflictError
from decimal import Decimal

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)


@router.post("/register", response_model=GenericResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Registra un nuevo usuario en el sistema.
    Requiere: email, password y access_code (string, ej: 'PROF2024').
    El access_level_id se obtiene automáticamente del código de acceso.
    """
    # Verificar si el email ya existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise ConflictError(f"El email {user_data.email} ya está registrado")
    
    # Buscar el código de acceso por el string (no por ID)
    from app.models.user import AccessCode
    access_code = db.query(AccessCode).filter(AccessCode.code == user_data.access_code).first()
    
    if not access_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El código de acceso '{user_data.access_code}' no existe o es inválido."
        )
    
    if not access_code.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de acceso no está activo."
        )
    
    # Verificar si el código ya fue usado (buscando usuarios que lo usaron)
    existing_user_with_code = db.query(User).filter(User.access_code_id == access_code.id).first()
    if existing_user_with_code:
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
        access_code_id=access_code.id,  # Usar el ID del código encontrado
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Limpiar relaciones antes de devolver
    user_response = UserResponse.model_validate(new_user)
    return created_response(data=user_response)


@router.post("/login", response_model=GenericResponse[Token])
async def login(
    login_data: UserLogin,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Autentica un usuario con validación de IMEI y coordenadas, y retorna un token JWT.
    Requiere: email, password, imei (15 dígitos) y coordenadas (latitude, longitude).
    """
    # Buscar usuario por email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user:
        raise UnauthorizedError("Credenciales inválidas")
    
    if not verify_password(login_data.password, user.password_hash):
        raise UnauthorizedError("Credenciales inválidas")
    
    if not user.is_active:
        raise UnauthorizedError("Usuario inactivo")
    
    # Validar formato del identificador del dispositivo
    if not validate_imei(login_data.imei):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador del dispositivo inválido. Debe ser una combinación válida de Build.FINGERPRINT + Build.ID."
        )
    
    # Validar que las coordenadas estén dentro de México
    is_valid, error_message = validate_coordinates(
        login_data.latitude, 
        login_data.longitude
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_message
        )
    
    # Buscar o crear dispositivo
    device = db.query(Device).filter(
        Device.user_id == user.id,
        Device.imei == login_data.imei
    ).first()
    
    if device:
        # Actualizar coordenadas y último login
        device.latitude = Decimal(str(login_data.latitude))
        device.longitude = Decimal(str(login_data.longitude))
        device.last_login_at = datetime.utcnow()
        device.is_active = True
    else:
        # Crear nuevo dispositivo
        device = Device(
            user_id=user.id,
            imei=login_data.imei,
            latitude=Decimal(str(login_data.latitude)),
            longitude=Decimal(str(login_data.longitude)),
            is_active=True,
            last_login_at=datetime.utcnow()
        )
        db.add(device)
    
    db.commit()
    
    # Crear token JWT (sub debe ser string según JWT spec)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "access_level_id": user.access_level_id}
    )
    
    token_data = Token(
        access_token=access_token,
        token_type="bearer"
    )
    return success_response(data=token_data)


@router.get("/me", response_model=GenericResponse[UserResponse])
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Obtiene la información del usuario autenticado.
    """
    user_response = UserResponse.model_validate(current_user)
    return success_response(data=user_response)

