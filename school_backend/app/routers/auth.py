"""
Router para autenticación y gestión de usuarios.
"""
from typing import Annotated
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.device import Device
from app.schemas.user import UserCreate, UserRegister, UserResponse, UserMeResponse, Token, UserLogin, RefreshTokenRequest
from app.schemas.response import GenericResponse, success_response, created_response
from app.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_refresh_token, validate_imei, validate_coordinates
from app.models.refresh_token import RefreshToken
from app.dependencies import get_current_user
from app.exceptions import UnauthorizedError, ConflictError, InactiveUserError
from app.config import settings
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
    
    # Crear nuevo usuario (is_active se establece automáticamente por el default de la BD)
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=None,  # Se puede actualizar después
        last_name=None,   # Se puede actualizar después
        phone=None,       # Se puede actualizar después
        access_level_id=access_level_id,
        access_code_id=access_code.id  # Usar el ID del código encontrado
        # is_active no se establece explícitamente, usa el DEFAULT TRUE de la BD
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
        raise InactiveUserError("Usuario inactivo")
    
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
    
    # Crear access token (20 minutos)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "access_level_id": user.access_level_id}
    )
    
    # Crear refresh token (3 meses)
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    # Calcular fecha de expiración del refresh token (3 meses)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Guardar refresh token en la base de datos
    refresh_token_db = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        is_active=True,
        expires_at=expires_at
    )
    db.add(refresh_token_db)
    db.commit()
    
    token_data = Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )
    return success_response(data=token_data)


@router.post("/refresh", response_model=GenericResponse[Token])
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Renueva el access token usando un refresh token válido.
    Requiere: refresh_token
    """
    # Decodificar y validar el refresh token
    try:
        payload = decode_refresh_token(refresh_data.refresh_token)
    except HTTPException:
        raise UnauthorizedError("Refresh token inválido o expirado")
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Refresh token inválido")
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise UnauthorizedError("Refresh token inválido: ID de usuario inválido")
    
    # Verificar que el usuario existe y está activo
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedError("Usuario no encontrado")
    
    if not user.is_active:
        raise UnauthorizedError("Usuario inactivo")
    
    # Verificar que el refresh token existe en la base de datos y está activo
    refresh_token_db = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_data.refresh_token,
        RefreshToken.user_id == user_id,
        RefreshToken.is_active == True
    ).first()
    
    if not refresh_token_db:
        raise UnauthorizedError("Refresh token no encontrado o inactivo")
    
    # Verificar que no haya expirado (verificación adicional)
    if refresh_token_db.expires_at < datetime.utcnow():
        # Invalidar el token expirado
        refresh_token_db.is_active = False
        db.commit()
        raise UnauthorizedError("Refresh token expirado")
    
    # Generar nuevo access token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "access_level_id": user.access_level_id}
    )
    
    # Opcional: invalidar el refresh token anterior y crear uno nuevo (rotación)
    # Por ahora, devolvemos el mismo refresh token
    # Si quieres rotación de tokens, descomenta las siguientes líneas:
    # refresh_token_db.is_active = False
    # new_refresh_token = create_refresh_token(
    #     data={"sub": str(user.id), "email": user.email}
    # )
    # expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    # new_refresh_token_db = RefreshToken(
    #     user_id=user.id,
    #     token=new_refresh_token,
    #     is_active=True,
    #     expires_at=expires_at
    # )
    # db.add(new_refresh_token_db)
    # db.commit()
    # refresh_token = new_refresh_token
    
    token_data = Token(
        access_token=access_token,
        refresh_token=refresh_data.refresh_token,  # Mantener el mismo refresh token
        token_type="bearer"
    )
    return success_response(data=token_data)


@router.get("/me", response_model=GenericResponse[UserMeResponse])
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Obtiene la información del usuario autenticado.
    """
    user_response = UserMeResponse.model_validate(current_user)
    return success_response(data=user_response)

