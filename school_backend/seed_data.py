"""
Script para poblar la base de datos con datos iniciales (catálogos).
Ejecuta este script después de crear la base de datos.
"""
from app.database import SessionLocal
from app.models.catalog import AccessLevel, SchoolType, Shift, School
from app.models.user import User
from app.security import get_password_hash

def seed_catalog_data():
    """Puebla las tablas de catálogos con datos iniciales."""
    db = SessionLocal()
    
    try:
        # Verificar si ya hay datos
        existing_levels = db.query(AccessLevel).count()
        existing_types = db.query(SchoolType).count()
        existing_shifts = db.query(Shift).count()
        existing_schools = db.query(School).count()

        if existing_levels > 0 and existing_types > 0 and existing_shifts > 0 and existing_schools > 0:
            print("✅ Los catálogos ya están poblados.")
        else:
            print("📦 Poblando catálogos...")
        
        # Niveles de acceso (según el schema SQL: Administrador, Profesor, Estudiante, PadreFamilia)
        access_levels = [
            {"name": "Administrador"},
            {"name": "Profesor"},
            {"name": "Estudiante"},
            {"name": "PadreFamilia"}
        ]
        
        for level_data in access_levels:
            existing = db.query(AccessLevel).filter(
                AccessLevel.name == level_data["name"]
            ).first()
            
            if not existing:
                level = AccessLevel(**level_data)
                db.add(level)
                print(f"  ✓ Nivel de acceso creado: {level_data['name']}")
        
        # Tipos de escuela (según el schema SQL)
        school_types = [
            {"name": "Preescolar"},
            {"name": "Primaria"},
            {"name": "Secundaria"},
            {"name": "Bachillerato"}
        ]
        
        for type_data in school_types:
            existing = db.query(SchoolType).filter(
                SchoolType.name == type_data["name"]
            ).first()
            
            if not existing:
                school_type = SchoolType(**type_data)
                db.add(school_type)
                print(f"  ✓ Tipo de escuela creado: {type_data['name']}")
        
        # Turnos (según el schema SQL)
        shifts = [
            {"name": "Matutino"},
            {"name": "Vespertino"},
            {"name": "Diurno"},
            {"name": "Completo"}
        ]
        
        for shift_data in shifts:
            existing = db.query(Shift).filter(
                Shift.name == shift_data["name"]
            ).first()
            
            if not existing:
                shift = Shift(**shift_data)
                db.add(shift)
                print(f"  ✓ Turno creado: {shift_data['name']}")
        
        schools = [
            {"cct": "15EPR0597V", "school_type_id": 1, "name": "Amado Nervo", "postal_code": "54070", "latitude": 19.529961, "longitude": -99.187095, "shift_id": 1},
            {"cct": "15EPR0596W", "school_type_id": 1, "name": "JAIME NUNO", "postal_code": "54026", "latitude": 19.559397, "longitude": -99.214712, "shift_id": 1},
            {"cct": "15DPR0906K", "school_type_id": 1, "name": "20 DE NOVIEMBRE", "postal_code": "54140", "latitude": 19.543918, "longitude": -99.154875, "shift_id": 1}
        ]
        for school_data in schools:
            existing = db.query(School).filter(
                School.cct == school_data["cct"]
            ).first()
            
            if not existing:
                school = School(**school_data)
                db.add(school)
                print(f"  ✓ Escuela creada: {school_data['name']}")
        
        db.commit()
        
        if existing_levels == 0 or existing_types == 0 or existing_shifts == 0 or existing_schools == 0:
            print("\n✅ Catálogos poblados exitosamente!")
        
        # Mostrar resumen
        print("\n📊 Resumen de catálogos creados:")
        levels = db.query(AccessLevel).all()
        print(f"  Niveles de acceso: {len(levels)}")
        for level in levels:
            print(f"    - ID: {level.id}, Nombre: {level.name}")
        
        types = db.query(SchoolType).all()
        print(f"\n  Tipos de escuela: {len(types)}")
        for st in types:
            print(f"    - ID: {st.id}, Nombre: {st.name}")
        
        shifts_list = db.query(Shift).all()
        print(f"\n  Turnos: {len(shifts_list)}")
        for shift in shifts_list:
            print(f"    - ID: {shift.id}, Nombre: {shift.name}")


        schools_list = db.query(School).all()
        print(f"\n  Escuelas: {len(schools_list)}")
        for school in schools_list:
            print(f"    - ID: {school.id}, Nombre: {school.name}")
        
        # Crear usuario administrador por defecto (siempre verificar)
        print("\n👤 Verificando usuario administrador...")
        admin_email = "admin@sistema.edu"
        admin_password = "Admin123!"  # Contraseña por defecto
        
        # Buscar el nivel de acceso Administrador
        admin_level = db.query(AccessLevel).filter(AccessLevel.name == "Administrador").first()
        
        if admin_level:
            # Verificar si ya existe un usuario administrador
            existing_admin = db.query(User).filter(User.email == admin_email).first()
            
            if not existing_admin:
                admin_user = User(
                    email=admin_email,
                    password_hash=get_password_hash(admin_password),
                    first_name="Administrador",
                    last_name="Sistema",
                    access_level_id=admin_level.id,
                    access_code_id=None,
                    is_active=True
                )
                db.add(admin_user)
                db.commit()
                db.refresh(admin_user)
                print(f"  ✓ Usuario administrador creado:")
                print(f"    Email: {admin_email}")
                print(f"    Contraseña: {admin_password}")
                print(f"    ⚠️  IMPORTANTE: Cambia esta contraseña después del primer inicio de sesión")
            else:
                print(f"  ℹ️  Usuario administrador ya existe: {admin_email}")
        else:
            print("  ⚠️  No se encontró el nivel de acceso 'Administrador'")


    except Exception as e:
        db.rollback()
        print(f"\n❌ Error al poblar catálogos: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Poblado de Datos Iniciales - Sistema Escolar")
    print("=" * 60)
    print()
    seed_catalog_data()

