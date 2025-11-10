"""
Módulo de seguridad para autenticación y autorización.
Gestiona hash de contraseñas y tokens JWT.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
import bcrypt
import math
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


def validate_imei(imei: str) -> bool:
    """
    Valida el formato del identificador del dispositivo.
    El IMEI debe ser una combinación de Build.FINGERPRINT + Build.ID (formato Android).
    
    Args:
        imei: Identificador del dispositivo (Build.FINGERPRINT + Build.ID)
        
    Returns:
        True si el identificador es válido, False en caso contrario
    """
    if not imei or len(imei.strip()) == 0:
        return False
    
    # Validar longitud mínima (Build.FINGERPRINT + Build.ID debe tener al menos algunos caracteres)
    if len(imei) < 10:
        return False
    
    # Validar longitud máxima (Build.FINGERPRINT puede ser largo, pero no excesivamente)
    if len(imei) > 500:
        return False
    
    # El formato Build.FINGERPRINT + Build.ID puede contener letras, números, guiones, puntos, etc.
    # No debe estar vacío después de quitar espacios
    if not imei.strip():
        return False
    
    return True


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia en kilómetros entre dos puntos geográficos usando la fórmula de Haversine.
    
    Args:
        lat1: Latitud del primer punto
        lon1: Longitud del primer punto
        lat2: Latitud del segundo punto
        lon2: Longitud del segundo punto
        
    Returns:
        Distancia en kilómetros
    """
    # Radio de la Tierra en kilómetros
    R = 6371.0
    
    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferencia de coordenadas
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def validate_coordinates(latitude: float, longitude: float) -> Tuple[bool, Optional[str]]:
    """
    Valida que las coordenadas del dispositivo estén dentro del territorio de México.
    
    Límites aproximados de México:
    - Latitud: 14.5°N a 32.7°N
    - Longitud: -118.4°W a -86.8°W
    
    Args:
        latitude: Latitud a validar
        longitude: Longitud a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    # Validar rango básico de coordenadas
    if not (-90.0 <= latitude <= 90.0):
        return False, "Latitud inválida. Debe estar entre -90 y 90 grados."
    
    if not (-180.0 <= longitude <= 180.0):
        return False, "Longitud inválida. Debe estar entre -180 y 180 grados."
    
    # Límites geográficos de México
    MEXICO_MIN_LAT = 14.5
    MEXICO_MAX_LAT = 32.7
    MEXICO_MIN_LON = -118.4
    MEXICO_MAX_LON = -86.8
    
    # Validar que las coordenadas estén dentro de México
    if not (MEXICO_MIN_LAT <= latitude <= MEXICO_MAX_LAT):
        return False, (
            f"Las coordenadas no están dentro del territorio de México. "
            f"Latitud: {latitude:.6f} (rango válido: {MEXICO_MIN_LAT}° a {MEXICO_MAX_LAT}°). "
            f"Esto podría indicar un intento de acceso no autorizado."
        )
    
    if not (MEXICO_MIN_LON <= longitude <= MEXICO_MAX_LON):
        return False, (
            f"Las coordenadas no están dentro del territorio de México. "
            f"Longitud: {longitude:.6f} (rango válido: {MEXICO_MIN_LON}° a {MEXICO_MAX_LON}°). "
            f"Esto podría indicar un intento de acceso no autorizado."
        )
    
    return True, None

