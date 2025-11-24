# 📋 Instrucciones: Crear Datos Iniciales (Catálogos)

## ⚠️ Problema Común: Error 500 al Registrar Usuario

Si estás obteniendo un error 500 al intentar registrar un usuario, es porque **faltan los datos iniciales en las tablas de catálogos**.

## 🔧 Solución: Poblar Catálogos

Antes de registrar usuarios, necesitas crear los datos iniciales en las tablas de catálogos:

1. **Niveles de acceso** (`access_levels`)
2. **Tipos de escuela** (`school_types`)
3. **Turnos** (`shifts`)

## 📝 Pasos para Poblar los Catálogos

### Opción 1: Usar el Script Python (Recomendado)

Ejecuta el script que creamos:

```bash
cd school_backend
python3 seed_data.py
```

Esto creará:
- **Niveles de acceso**: Administrador, Profesor, Estudiante, PadreFamilia
- **Tipos de escuela**: Preescolar, Primaria, Secundaria, Bachillerato
- **Turnos**: Matutino, Vespertino, Diurno, Completo

### Opción 2: Insertar Datos Manualmente con SQL

Si prefieres hacerlo manualmente, ejecuta estos comandos SQL:

```sql
-- Conectarte a MySQL
mysql -u root -p re_db

-- Catálogos: school_types
INSERT INTO school_types (name) VALUES
('Preescolar'),('Primaria'), ('Secundaria'), ('Bachillerato'), ('Universidad')
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- Catálogos: shifts
INSERT INTO shifts (name) VALUES
('Matutino'), ('Vespertino'), ('Diurno'), ('Completo')
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- Catálogos: access_levels
INSERT INTO access_levels (name) VALUES
('Administrador'), ('Profesor'), ('Estudiante'), ('PadreFamilia')
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- Catálogos: schools
INSERT INTO schools (cct, school_type_id, name, postal_code, latitude, longitude, shift_id)
VALUES ('15EPR0597V', 2, 'Amado Nervo', '54070', 19.529961, -99.187095, 1),
('15EPR0596W', 2, 'JAIME NUNO', '54026', 19.559397, -99.214712, 1),
('15DPR0906K', 2, '20 DE NOVIEMBRE', '54140', 19.543918, -99.154875, 1)
ON DUPLICATE KEY UPDATE name = VALUES(name);
```

## ✅ Verificar que los Datos se Crearon

Después de ejecutar el script, puedes verificar:

```bash
cd school_backend
python3 -c "
from app.database import SessionLocal
from app.models.catalog import AccessLevel, SchoolType, Shift

db = SessionLocal()
try:
    levels = db.query(AccessLevel).all()
    print('Niveles de acceso:')
    for level in levels:
        print(f'  ID: {level.id}, Nombre: {level.name}')
finally:
    db.close()
"
```

## 🎯 Registrar Usuario Correctamente

Una vez que los catálogos estén creados, puedes registrar un usuario usando un `access_level_id` válido:

```json
{
  "email": "user@example.com",
  "first_name": "Nombre",
  "last_name": "Usuario",
  "phone": null,
  "access_level_id": 1,  // ← Usa un ID válido (1, 2, 3 o 4)
  "access_code_id": null, // ← Puede ser null si no usas código de acceso
  "is_active": true,
  "password": "password123"
}
```

### IDs Válidos Después de Poblar Catálogos:

- **access_level_id**: 1 (Administrador), 2 (Profesor), 3 (Estudiante), 4 (PadreFamilia)
- **access_code_id**: null (opcional, si usas códigos de acceso)
- **school_type_id**: 1, 2, 3 o 4 (cuando crees escuelas)

## 📌 Notas Importantes

1. **access_level_id es OBLIGATORIO**: Debe ser un ID válido que exista en `access_levels`
2. **access_code_id es OPCIONAL**: Puede ser `null` si no usas códigos de acceso para registro
3. **Los catálogos solo se crean una vez**: El script verifica si ya existen antes de crearlos

## 🐛 Solución de Problemas

### Error: "Access denied for user 'root'"
- Verifica que el archivo `.env` tenga las credenciales correctas de MySQL
- Asegúrate de que MySQL esté ejecutándose: `brew services list`

### Error: "Table doesn't exist"
- Ejecuta primero el script de creación de base de datos: `python3 setup_database.py`

### Error: "El nivel de acceso especificado no existe"
- Ejecuta el script de datos iniciales: `python3 seed_data.py`
- Verifica que los catálogos se crearon correctamente

