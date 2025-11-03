"""
Script para crear el archivo .env con las credenciales de MySQL.
Ejecuta este script y sigue las instrucciones.
"""
import os
import secrets

def generate_secret_key():
    """Genera una clave secreta aleatoria para JWT."""
    return secrets.token_hex(32)

def create_env_file():
    """Crea el archivo .env con las configuraciones."""
    
    print("=" * 60)
    print("Configuración del archivo .env para MySQL")
    print("=" * 60)
    print()
    
    # Si el archivo ya existe, preguntar si sobrescribir
    if os.path.exists(".env"):
        response = input("El archivo .env ya existe. ¿Deseas sobrescribirlo? (s/N): ")
        if response.lower() != 's':
            print("Operación cancelada.")
            return
    
    # Solicitar información de MySQL
    print("Por favor, ingresa la información de tu base de datos MySQL:")
    print()
    
    database_host = input("Host de MySQL [localhost]: ").strip() or "localhost"
    database_port = input("Puerto de MySQL [3306]: ").strip() or "3306"
    database_user = input("Usuario de MySQL [root]: ").strip() or "root"
    database_password = input("Contraseña de MySQL (deja vacío si no tienes): ").strip()
    database_name = input("Nombre de la base de datos [re_db]: ").strip() or "re_db"
    
    print()
    use_custom_secret = input("¿Deseas generar una nueva clave secreta JWT? (S/n): ").strip().lower()
    if use_custom_secret != 'n':
        secret_key = generate_secret_key()
        print(f"Clave secreta generada: {secret_key}")
    else:
        secret_key = "197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3"
    
    # Crear contenido del archivo .env
    env_content = f"""# ============================================
# Configuración del Sistema Escolar Backend
# ============================================

# Configuración de la aplicación
APP_NAME=Sistema Escolar Backend
APP_VERSION=1.0.0
DEBUG=True

# ============================================
# Configuración de Base de Datos MySQL
# ============================================
DATABASE_HOST={database_host}
DATABASE_PORT={database_port}
DATABASE_USER={database_user}
DATABASE_PASSWORD={database_password}
DATABASE_NAME={database_name}

# Opcional: Si prefieres usar una URL completa de conexión, descomenta la siguiente línea
# DATABASE_URL=mysql+pymysql://{database_user}:{database_password}@{database_host}:{database_port}/{database_name}?charset=utf8mb4

# ============================================
# Configuración de Seguridad JWT
# ============================================
# ⚠️ IMPORTANTE: Cambia este SECRET_KEY en producción
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ============================================
# Configuración de CORS
# ============================================
# Para desarrollo: usar "*" permite todos los orígenes
# Para producción: especifica los orígenes permitidos separados por comas
CORS_ORIGINS=*
"""
    
    # Escribir el archivo
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        
        print()
        print("=" * 60)
        print("✅ Archivo .env creado exitosamente!")
        print("=" * 60)
        print()
        print("📝 Configuración guardada:")
        print(f"   - Host: {database_host}")
        print(f"   - Puerto: {database_port}")
        print(f"   - Usuario: {database_user}")
        print(f"   - Base de datos: {database_name}")
        print()
        print("⚠️  IMPORTANTE:")
        print("   1. Asegúrate de que MySQL esté ejecutándose")
        print("   2. Ejecuta el script SQL para crear las tablas:")
        print("      mysql -u {database_user} -p < '../Database Scripts/MySQLScript.sql'")
        print("   3. O importa el script desde MySQL Workbench")
        print()
        print("🚀 Para ejecutar la aplicación:")
        print("   python run.py")
        print("   o")
        print("   uvicorn app.main:app --reload")
        print()
        
    except Exception as e:
        print(f"❌ Error al crear el archivo .env: {e}")

if __name__ == "__main__":
    create_env_file()

