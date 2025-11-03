# 🗄️ Guía de Instalación de MySQL

Como MySQL no está instalado en tu sistema, aquí tienes varias opciones para instalarlo.

## Opción 1: Instalar MySQL con Homebrew (Recomendado para macOS)

### Paso 1: Instalar MySQL

```bash
brew install mysql
```

### Paso 2: Iniciar el servicio MySQL

```bash
# Si instalaste MySQL 8.4 (versión específica)
brew services start mysql@8.4

# O si instalaste MySQL estándar
brew services start mysql

# O iniciarlo solo una vez
mysql.server start
```

**Nota:** Si instalaste `mysql@8.4`, necesitarás añadirlo al PATH. Añade esta línea a tu `~/.zshrc`:
```bash
echo 'export PATH="/opt/homebrew/opt/mysql@8.4/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Paso 3: Configurar MySQL (opcional)

```bash
mysql_secure_installation
```

Este comando te permitirá:
- Establecer una contraseña para root
- Remover usuarios anónimos
- Desactivar login remoto para root
- Remover la base de datos de prueba

### Paso 4: Verificar la instalación

```bash
mysql -u root -p
```

Si funciona, puedes salir con `exit` o `\q`

## Opción 2: Usar Docker (Más rápido y limpio)

Si prefieres no instalar MySQL directamente, puedes usar Docker:

### Paso 1: Instalar Docker Desktop

Descarga desde: https://www.docker.com/products/docker-desktop

### Paso 2: Ejecutar MySQL en Docker

```bash
docker run --name mysql-school \
  -e MYSQL_ROOT_PASSWORD=tu_password \
  -e MYSQL_DATABASE=re_db \
  -p 3306:3306 \
  -d mysql:8.0

# O sin contraseña para desarrollo
docker run --name mysql-school \
  -e MYSQL_ALLOW_EMPTY_PASSWORD=yes \
  -e MYSQL_DATABASE=re_db \
  -p 3306:3306 \
  -d mysql:8.0
```

### Paso 3: Verificar que está corriendo

```bash
docker ps
```

Deberías ver el contenedor `mysql-school` en ejecución.

### Paso 4: Detener/Iniciar el contenedor cuando sea necesario

```bash
# Detener
docker stop mysql-school

# Iniciar
docker start mysql-school

# Ver logs
docker logs mysql-school
```

## Opción 3: Usar el script Python (Sin necesidad de MySQL CLI)

Si no quieres instalar MySQL CLI pero MySQL está ejecutándose, puedes usar el script Python:

### Paso 1: Asegúrate de tener MySQL ejecutándose

Si instalaste con Homebrew:
```bash
brew services start mysql
```

### Paso 2: Ejecutar el script Python

```bash
cd school_backend
python setup_database.py
```

Este script:
- Se conecta directamente usando PyMySQL
- Lee el archivo SQL
- Crea la base de datos y todas las tablas
- Verifica que todo se haya creado correctamente

## Configuración del archivo .env

Una vez que MySQL esté instalado y ejecutándose, actualiza tu archivo `.env`:

### Si instalaste con Homebrew (sin contraseña por defecto):
```env
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=
DATABASE_NAME=re_db
```

### Si instalaste con Homebrew (con contraseña):
```env
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=tu_contraseña
DATABASE_NAME=re_db
```

### Si usas Docker:
```env
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=tu_password  # o vacío si usaste MYSQL_ALLOW_EMPTY_PASSWORD
DATABASE_NAME=re_db
```

## Verificar la conexión

Puedes verificar que todo está configurado correctamente:

```bash
# Desde Python
cd school_backend
python -c "from app.config import settings; print(f'URL: {settings.database_url}')"

# O probar la conexión directamente
python setup_database.py
```

## Comandos útiles de MySQL

Una vez instalado, puedes usar:

```bash
# Conectarte a MySQL
mysql -u root -p

# Ver bases de datos
mysql -u root -p -e "SHOW DATABASES;"

# Ver tablas de una base de datos
mysql -u root -p -e "USE re_db; SHOW TABLES;"
```

## Solución de problemas

### Error: "Cannot upgrade from 80100 to 90500" o "Data Dictionary initialization failed"

Este error ocurre cuando intentas ejecutar MySQL 9.x con datos de MySQL 8.1. MySQL 9.x solo permite actualizaciones directas desde MySQL 8.0 LTS.

**Solución:**

1. Detén MySQL:
   ```bash
   brew services stop mysql
   ```

2. Desinstala MySQL 9.x:
   ```bash
   brew uninstall mysql
   ```

3. Instala MySQL 8.4 (versión intermedia compatible):
   ```bash
   brew install mysql@8.4
   ```

4. Añade MySQL 8.4 al PATH (añade esta línea a tu `~/.zshrc` o `~/.bash_profile`):
   ```bash
   echo 'export PATH="/opt/homebrew/opt/mysql@8.4/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

5. Inicia MySQL 8.4:
   ```bash
   brew services start mysql@8.4
   ```

6. Verifica que funciona:
   ```bash
   mysql -u root -e "SELECT VERSION();"
   ```

MySQL 8.4 actualizará automáticamente tus datos desde MySQL 8.1. Una vez que todo funcione correctamente, podrás actualizar a MySQL 9.x si lo deseas.

### Error: "Can't connect to MySQL server"

1. Verifica que MySQL esté ejecutándose:
   ```bash
   # Con Homebrew
   brew services list
   
   # O verifica los procesos
   ps aux | grep mysql
   ```

2. Inicia MySQL si no está corriendo:
   ```bash
   # Para MySQL 8.4
   brew services start mysql@8.4
   
   # O para MySQL estándar
   brew services start mysql
   ```

### Error: "Access denied"

1. Intenta conectarte sin contraseña primero:
   ```bash
   mysql -u root
   ```

2. Si no funciona, resetea la contraseña:
   ```bash
   sudo /usr/local/mysql/support-files/mysql.server stop
   sudo /usr/local/mysql/bin/mysqld_safe --skip-grant-tables &
   mysql -u root
   ```

### Puerto 3306 ya en uso

Si el puerto ya está en uso, puedes:
1. Cambiar el puerto en Docker:
   ```bash
   docker run -p 3307:3306 ...
   ```
   Y actualizar `DATABASE_PORT=3307` en `.env`

2. O detener el proceso que está usando el puerto:
   ```bash
   lsof -i :3306
   kill -9 <PID>
   ```

