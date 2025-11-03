"""
Dependencias reutilizables para los routers.
Incluye autenticación, autorización y validaciones comunes.
"""
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.security import decode_access_token
from app.models.user import User
from app.exceptions import UnauthorizedError, ForbiddenError

# Configuración OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    """
    Obtiene el usuario actual desde el token JWT.
    
    Args:
        token: Token JWT del header Authorization
        db: Sesión de base de datos
        
    Returns:
        Objeto User del usuario autenticado
        
    Raises:
        UnauthorizedError: Si el token es inválido o el usuario no existe
    """
    payload = decode_access_token(token)
    user_id: Optional[int] = payload.get("sub")
    
    if user_id is None:
        raise UnauthorizedError("Token inválido")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedError("Usuario no encontrado")
    
    if not user.is_active:
        raise UnauthorizedError("Usuario inactivo")
    
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Verifica que el usuario esté activo."""
    if not current_user.is_active:
        raise UnauthorizedError("Usuario inactivo")
    return current_user


def require_access_level(*allowed_levels: str):
    """
    Decorador para requerir niveles de acceso específicos.
    
    Usage:
        @router.get("/admin")
        def admin_endpoint(user = Depends(require_access_level("admin", "super_admin"))):
            ...
    """
    def check_access(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        # Obtener el nombre del nivel de acceso del usuario
        access_level_name = current_user.access_level.name if current_user.access_level else None
        
        if access_level_name not in allowed_levels:
            raise ForbiddenError(
                f"Se requiere uno de los siguientes niveles: {', '.join(allowed_levels)}"
            )
        return current_user
    
    return check_access

