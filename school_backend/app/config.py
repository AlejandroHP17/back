"""
Configuración centralizada del sistema escolar.
Gestiona variables de entorno y configuraciones de la aplicación.
"""
try:
    from pydantic_settings import BaseSettings  # type: ignore
except ImportError:
    from pydantic import BaseSettings  # type: ignore

from typing import Optional, List


class Settings(BaseSettings):
    """Configuración de la aplicación desde variables de entorno."""
    
    # Configuración de la aplicación
    APP_NAME: str = "Sistema Escolar Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Configuración de base de datos MySQL
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = ""
    DATABASE_NAME: str = "re_db"
    DATABASE_URL: Optional[str] = None
    
    # Configuración de seguridad JWT
    SECRET_KEY: str = "197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 20  # 20 minutos
    REFRESH_TOKEN_EXPIRE_DAYS: int = 90  # 3 meses (90 días)
    
    # Configuración de CORS (puede ser un string separado por comas o "*")
    CORS_ORIGINS: str = "*"
    
    @property
    def database_url(self) -> str:
        """Construye la URL de conexión a la base de datos."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
            f"?charset=utf8mb4"
        )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

