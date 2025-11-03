"""
Módulo de seguridad para autenticación y autorización.
Gestiona hash de contraseñas y tokens JWT.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
import bcrypt
from fastapi import HTTPException, status
from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña plana coincide con el hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Genera un hash bcrypt para la contraseña."""
    # Generar salt y hash la contraseña
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea un token JWT de acceso.
    
    Args:
        data: Datos a incluir en el token (usuario, roles, etc.)
        expires_delta: Tiempo de expiración personalizado
        
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # El "exp" debe ser un timestamp (número), no un datetime
    # jwt.encode acepta datetime y lo convierte automáticamente, pero asegurémonos
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decodifica y valida un token JWT.
    
    Args:
        token: Token JWT a decodificar
        
    Returns:
        Payload del token
        
    Raises:
        HTTPException: Si el token es inválido o ha expirado
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no proporcionado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Limpiar espacios en blanco al inicio y final
    token = token.strip()
    
    # Validar formato básico del token (debe tener 3 partes separadas por puntos)
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token con formato inválido: debe tener 3 partes separadas por puntos, pero tiene {len(parts)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validar que cada parte no esté vacía
    for i, part in enumerate(parts, 1):
        if not part:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token inválido: la parte {i} está vacía. El token parece estar incompleto o corrupto.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Validar longitud mínima de cada parte (un JWT válido tiene partes de cierto tamaño)
    # La tercera parte (signature) debe tener al menos 43 caracteres para un token válido
    if len(parts[2]) < 20:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: la firma del token parece estar incompleta (longitud: {len(parts[2])} caracteres). El token puede estar truncado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        error_message = str(e)
        
        # Mensaje más específico para el error de padding
        if "padding" in error_message.lower():
            detail = (
                "Token inválido: error de padding criptográfico. "
                "Esto generalmente indica que el token está incompleto, truncado o corrupto. "
                "Asegúrate de copiar el token completo desde el login."
            )
        else:
            detail = f"Token inválido: {error_message}"
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

