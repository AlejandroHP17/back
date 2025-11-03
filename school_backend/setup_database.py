"""
Script para crear la base de datos y tablas directamente desde Python.
Útil cuando MySQL no está en el PATH o prefieres no usar la línea de comandos.
"""
import sys
import os
from sqlalchemy import create_engine, text
from app.config import settings

def create_database():
    """Crea la base de datos y las tablas usando PyMySQL."""
    
    print("=" * 60)
    print("Configuración de Base de Datos MySQL")
    print("=" * 60)
    print()
    
    # Leer el archivo SQL (intentar primero el archivo local, luego el original)
    sql_file_path = "database_schema.sql"
    #if not os.path.exists(sql_file_path):
    #    sql_file_path = "../Database Scripts/MySQLScript.sql"
    
    try:
        with open(sql_file_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {sql_file_path}")
        print("   Asegúrate de ejecutar este script desde la carpeta school_backend")
        sys.exit(1)
    
    print(f"📄 Archivo SQL encontrado: {sql_file_path}")
    print()
    
    # Crear conexión temporal sin especificar la base de datos
    # Necesitamos conectarnos primero para crear la base de datos
    temp_url = (
        f"mysql+pymysql://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}"
        f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}"
    )
    
    print("🔌 Conectando a MySQL...")
    print(f"   Host: {settings.DATABASE_HOST}")
    print(f"   Puerto: {settings.DATABASE_PORT}")
    print(f"   Usuario: {settings.DATABASE_USER}")
    print()
    
    try:
        # Crear conexión temporal
        temp_engine = create_engine(temp_url, echo=False)
        
        with temp_engine.connect() as conn:
            # Primero, crear la base de datos si no existe
            print(f"📦 Creando base de datos '{settings.DATABASE_NAME}' si no existe...")
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.DATABASE_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.execute(text(f"USE {settings.DATABASE_NAME}"))
            conn.commit()
            print(f"✅ Base de datos '{settings.DATABASE_NAME}' creada/existe")
            print()
            
            # Desactivar verificación de claves foráneas temporalmente
            print("🔧 Configurando base de datos...")
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            conn.commit()
            
            # Ejecutar el script SQL
            print("📝 Ejecutando script SQL...")
            
            # Dividir el script en sentencias individuales
            statements = []
            current_statement = ""
            
            for line in sql_script.split('\n'):
                # Ignorar líneas vacías y comentarios simples
                stripped = line.strip()
                if not stripped or stripped.startswith('--') or stripped.startswith('#'):
                    continue
                
                current_statement += line + '\n'
                
                # Si la línea termina con ';', es el fin de una sentencia
                if ';' in line and not line.strip().startswith('--'):
                    # Extraer solo la parte antes del punto y coma
                    statements.append(current_statement)
                    current_statement = ""
            
            # Ejecutar cada sentencia
            executed = 0
            for stmt in statements:
                stmt = stmt.strip()
                if stmt and not stmt.upper().startswith('SET ') and 'FOREIGN_KEY_CHECKS' not in stmt.upper():
                    try:
                        conn.execute(text(stmt))
                        executed += 1
                    except Exception as e:
                        # Algunos errores son esperados (DROP DATABASE, etc.)
                        if "DROP DATABASE" in stmt.upper() or "USE" in stmt.upper():
                            pass
                        else:
                            print(f"⚠️  Advertencia en: {stmt[:50]}...")
                            print(f"   Error: {str(e)[:100]}")
            
            # Reactivar verificación de claves foráneas
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            conn.commit()
            
            print(f"✅ {executed} sentencias SQL ejecutadas exitosamente")
            print()
            
            # Verificar que las tablas se crearon
            print("🔍 Verificando tablas creadas...")
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            
            if tables:
                print(f"✅ {len(tables)} tablas creadas:")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("⚠️  No se encontraron tablas. Revisa el script SQL.")
            
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Error al conectar o ejecutar SQL")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        print("Posibles soluciones:")
        print("1. Verifica que MySQL esté ejecutándose")
        print("2. Verifica las credenciales en el archivo .env")
        print("3. Asegúrate de que el usuario tenga permisos")
        print()
        print("Para instalar MySQL en macOS:")
        print("   brew install mysql")
        print("   brew services start mysql")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✅ Base de datos configurada exitosamente!")
    print("=" * 60)
    print()
    print("🚀 Puedes ejecutar la aplicación con:")
    print("   python run.py")
    print()


if __name__ == "__main__":
    create_database()

