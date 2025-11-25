"""
Schemas para usuarios y códigos de acceso.
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Schema base para usuario."""
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    first_name: Optional[str] = Field(None, max_length=100, description="Nombre")
    last_name: Optional[str] = Field(None, max_length=100, description="Apellido")
    phone: Optional[str] = Field(None, max_length=30, description="Teléfono")
    access_level_id: int = Field(..., description="ID del nivel de acceso")
    access_code_id: Optional[int] = Field(None, description="ID del código de acceso usado al registrarse")
    is_active: bool = Field(True, description="Estado activo/inactivo")


class UserRegister(BaseModel):
    """Schema para registro de usuario (solo email, password y código)."""
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    password: str = Field(..., min_length=8, description="Contraseña del usuario")
    access_code: str = Field(..., min_length=1, max_length=50, description="Código de acceso (string, ej: 'PROF2024')")


class UserCreate(UserBase):
    """Schema para crear un usuario."""
    password: str = Field(..., min_length=8, description="Contraseña del usuario")


class UserUpdate(BaseModel):
    """Schema para actualizar un usuario."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    password: Optional[str] = Field(None, min_length=8)
    access_level_id: Optional[int] = None
    access_code_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema de respuesta para usuario."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserMeResponse(BaseModel):
    """Schema de respuesta para el endpoint /me (sin access_code_id)."""
    id: int
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    first_name: Optional[str] = Field(None, max_length=100, description="Nombre")
    last_name: Optional[str] = Field(None, max_length=100, description="Apellido")
    phone: Optional[str] = Field(None, max_length=30, description="Teléfono")
    access_level_id: int = Field(..., description="ID del nivel de acceso")
    is_active: bool = Field(True, description="Estado activo/inactivo")
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Schema para login de usuario con validación de seguridad."""
    email: EmailStr = Field(..., description="Correo electrónico")
    password: str = Field(..., description="Contraseña")
    imei: str = Field(..., min_length=1, max_length=500, description="Identificador único del dispositivo (Build.FINGERPRINT + Build.ID)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitud de la ubicación del dispositivo")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitud de la ubicación del dispositivo")


class Token(BaseModel):
    """Schema para tokens de acceso y refresco."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema para solicitud de renovación de token."""
    refresh_token: str = Field(..., description="Refresh token para renovar el access token")


class AccessCodeBase(BaseModel):
    """Schema base para código de acceso."""
    code: str = Field(..., min_length=1, max_length=50, description="Código de acceso")
    access_level_id: int = Field(..., description="ID del nivel de acceso")
    description: Optional[str] = Field(None, max_length=255, description="Descripción del código")
    is_active: bool = Field(True, description="Estado activo/inactivo")


class AccessCodeCreate(BaseModel):
    """Schema para crear un código de acceso."""
    code: str = Field(..., min_length=1, max_length=50, description="Código de acceso")
    access_level_id: int = Field(..., description="ID del nivel de acceso")
    description: Optional[str] = Field(None, max_length=255, description="Descripción del código")


class AccessCodeUpdate(BaseModel):
    """Schema para actualizar un código de acceso."""
    is_active: bool = Field(..., description="Estado activo/inactivo")


class AccessCodeResponse(AccessCodeBase):
    """Schema de respuesta para código de acceso."""
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

