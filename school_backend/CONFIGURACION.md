# 🔧 Guía de Configuración - Archivo .env

## Crear el archivo .env

Tienes dos opciones para crear el archivo `.env`:

### Opción 1: Usar el script automático (Recomendado)

Ejecuta el script que te ayudará a crear el archivo `.env`:

```bash
cd school_backend
python create_env.py
```

El script te pedirá:
- Host de MySQL (por defecto: `localhost`)
- Puerto de MySQL (por defecto: `3306`)
- Usuario de MySQL (por defecto: `root`)
- Contraseña de MySQL (deja vacío si no tienes)
- Nombre de la base de datos (por defecto: `re_db`)

### Opción 2: Crear manualmente el archivo .env

Crea un archivo llamado `.env` en la carpeta `school_backend` con el siguiente contenido:

```env
# ============================================
# Configuración del Sistema Escolar Backend
# ============================================

# Configuración de la aplicación
APP_NAME=Sistema Escolar Backend
APP_VERSION=1.0.0
DEBUG=True

# ============================================
# Configuración de Base de Datos MySQL
# ============================================
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=tu_contraseña_aqui
DATABASE_NAME=re_db

# ============================================
# Configuración de Seguridad JWT
# ============================================
SECRET_KEY=197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ============================================
# Configuración de CORS
# ============================================
CORS_ORIGINS=*
```

## ⚙️ Configuración detallada

### Configuración de MySQL

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `DATABASE_HOST` | Dirección del servidor MySQL | `localhost` |
| `DATABASE_PORT` | Puerto de MySQL | `3306` |
| `DATABASE_USER` | Usuario de MySQL | `root` |
| `DATABASE_PASSWORD` | Contraseña de MySQL | (vacío) |
| `DATABASE_NAME` | Nombre de la base de datos | `re_db` |

### Configuración de Seguridad

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `SECRET_KEY` | Clave secreta para JWT | (generada automáticamente) |
| `ALGORITHM` | Algoritmo de encriptación JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Tiempo de expiración del token (minutos) | `1440` (24 horas) |

### Generar una nueva SECRET_KEY

Para generar una nueva clave secreta segura, puedes usar:

```bash
# En Python
python -c "import secrets; print(secrets.token_hex(32))"

# O en la terminal
openssl rand -hex 32
```

## 📋 Pasos siguientes

1. **Crear el archivo .env** usando una de las opciones anteriores

2. **Crear la base de datos MySQL**:
   ```bash
   mysql -u root -p < "../Database Scripts/MySQLScript.sql"
   ```
   
   O desde MySQL Workbench:
   - Abre MySQL Workbench
   - Conecta a tu servidor MySQL
   - Abre el archivo `Database Scripts/MySQLScript.sql`
   - Ejecuta el script

3. **Verificar la conexión**:
   ```bash
   python -c "from app.config import settings; print(f'URL: {settings.database_url}')"
   ```

4. **Ejecutar la aplicación**:
   ```bash
   python run.py
   ```

## 🔒 Seguridad en Producción

⚠️ **IMPORTANTE**: Antes de desplegar en producción:

1. **Cambia el SECRET_KEY** por una clave segura y única
2. **Configura CORS_ORIGINS** con los dominios permitidos específicos:
   ```env
   CORS_ORIGINS=https://tudominio.com,https://www.tudominio.com
   ```
3. **Establece DEBUG=False**:
   ```env
   DEBUG=False
   ```
4. **Usa credenciales seguras** para la base de datos
5. **No subas el archivo .env** a repositorios públicos (ya está en .gitignore)

## ❓ Solución de problemas

### Error: "Can't connect to MySQL server"

- Verifica que MySQL esté ejecutándose:
  ```bash
  # En macOS/Linux
  brew services list  # o sudo systemctl status mysql
  
  # En Windows
  # Verifica desde Servicios de Windows
  ```

- Verifica las credenciales en el archivo `.env`

### Error: "Unknown database 're_db'"

- Ejecuta el script SQL para crear la base de datos:
  ```bash
  mysql -u root -p < "../Database Scripts/MySQLScript.sql"
  ```

### Error: "Access denied for user"

- Verifica que el usuario y contraseña sean correctos
- Asegúrate de que el usuario tenga permisos para crear/leer bases de datos

