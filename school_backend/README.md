# Sistema Escolar Backend

Backend desarrollado con FastAPI y Python para la gestión de un sistema escolar completo. Implementa arquitectura escalable siguiendo mejores prácticas.

## 🚀 Características

- **Arquitectura modular**: Separación clara de responsabilidades (models, schemas, services, routers)
- **Autenticación JWT**: Sistema seguro de autenticación con tokens
- **Base de datos MySQL**: Soporte completo para MySQL con SQLAlchemy ORM
- **Validación de datos**: Schemas Pydantic para validación automática
- **Documentación automática**: Swagger UI y ReDoc integrados
- **Manejo de errores**: Excepciones personalizadas y manejo centralizado
- **Escalable**: Estructura diseñada para crecer y mantenerse

## 📋 Requisitos

- Python 3.11+
- MySQL 8.0+
- pip o poetry

## 🔧 Instalación

1. **Clonar el repositorio** (si aplica)

2. **Crear entorno virtual**:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**:
```bash
cp .env.example .env
# Editar .env con tus credenciales de base de datos
```

5. **Crear la base de datos**:
```bash
# Ejecutar el script SQL proporcionado en Database Scripts/MySQLScript.sql
mysql -u root -p < "Database Scripts/MySQLScript.sql"
```

6. **Ejecutar la aplicación**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La aplicación estará disponible en `http://localhost:8000`

## 📚 Documentación de la API

Una vez que la aplicación esté ejecutándose, puedes acceder a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Estructura del Proyecto

```
school_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Aplicación principal FastAPI
│   ├── config.py               # Configuración centralizada
│   ├── database.py             # Configuración de base de datos
│   ├── security.py             # Utilidades de seguridad (JWT, hash)
│   ├── dependencies.py         # Dependencias reutilizables
│   ├── exceptions.py           # Excepciones personalizadas
│   ├── models/                 # Modelos SQLAlchemy
│   │   ├── base.py
│   │   ├── catalog.py
│   │   ├── school.py
│   │   ├── user.py
│   │   ├── cycle.py
│   │   ├── student.py
│   │   ├── partial.py
│   │   ├── learning_field.py
│   │   ├── work_type.py
│   │   ├── attendance.py
│   │   └── student_work.py
│   ├── schemas/                # Schemas Pydantic
│   │   ├── catalog.py
│   │   ├── school.py
│   │   ├── user.py
│   │   ├── cycle.py
│   │   ├── student.py
│   │   ├── partial.py
│   │   ├── learning_field.py
│   │   ├── work_type.py
│   │   ├── attendance.py
│   │   └── student_work.py
│   └── routers/                # Routers de la API
│       ├── auth.py
│       ├── schools.py
│       ├── students.py
│       └── cycles.py
├── requirements.txt
├── .env.example
└── README.md
```

## 🔐 Autenticación

El sistema utiliza autenticación JWT. Para usar los endpoints protegidos:

1. **Registrar un usuario**:
```bash
POST /api/auth/register
{
  "email": "usuario@example.com",
  "password": "password123",
  "full_name": "Nombre Usuario",
  "access_level_id": 1,
  "school_id": null,
  "is_active": true
}
```

2. **Iniciar sesión**:
```bash
POST /api/auth/login
# Form data:
# username: usuario@example.com
# password: password123
```

3. **Usar el token**:
```bash
Authorization: Bearer <token>
```

## 📝 Endpoints Principales

### Autenticación
- `POST /api/auth/register` - Registrar nuevo usuario
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/me` - Obtener información del usuario actual

### Escuelas
- `GET /api/schools` - Listar escuelas (con paginación y búsqueda)
- `GET /api/schools/{id}` - Obtener escuela por ID
- `POST /api/schools` - Crear escuela (requiere admin)
- `PUT /api/schools/{id}` - Actualizar escuela (requiere admin)
- `DELETE /api/schools/{id}` - Eliminar escuela (requiere super_admin)

### Estudiantes
- `GET /api/students` - Listar estudiantes
- `GET /api/students/{id}` - Obtener estudiante por ID
- `POST /api/students` - Crear estudiante
- `PUT /api/students/{id}` - Actualizar estudiante
- `DELETE /api/students/{id}` - Eliminar estudiante
- `POST /api/students/cycles/{cycle_id}/enroll` - Inscribir estudiante en ciclo

### Ciclos Escolares
- `GET /api/cycles` - Listar ciclos (con filtros)
- `GET /api/cycles/{id}` - Obtener ciclo por ID
- `POST /api/cycles` - Crear ciclo escolar
- `PUT /api/cycles/{id}` - Actualizar ciclo
- `DELETE /api/cycles/{id}` - Eliminar ciclo

## 🔒 Niveles de Acceso

El sistema soporta múltiples niveles de acceso definidos en `catalog_access_levels`. Algunos endpoints requieren niveles específicos:

- **Usuario regular**: Acceso básico
- **admin**: Permite gestión de escuelas
- **super_admin**: Acceso completo al sistema

## 🛠️ Desarrollo

### Ejecutar en modo desarrollo:
```bash
uvicorn app.main:app --reload
```

### Ejecutar tests (cuando estén implementados):
```bash
pytest
```

## 📄 Licencia

Este proyecto es un ejemplo educativo.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.

## 📞 Soporte

Para preguntas o problemas, por favor abre un issue en el repositorio.

