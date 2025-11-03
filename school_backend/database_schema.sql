-- ======================================================
-- Script: esquema_educativo.sql
-- Propósito: Crear tablas, constraints e insertar datos de ejemplo
-- Motor: MySQL (InnoDB), codificación utf8mb4
-- ======================================================

SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS re_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE re_db;

-- Elimina tablas en orden que evita violación FK
DROP TABLE IF EXISTS student_works;
DROP TABLE IF EXISTS attendances;
DROP TABLE IF EXISTS work_types;
DROP TABLE IF EXISTS formative_fields;
DROP TABLE IF EXISTS partials;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS school_cycles;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS access_codes;
DROP TABLE IF EXISTS schools;
DROP TABLE IF EXISTS access_levels;
DROP TABLE IF EXISTS shifts;
DROP TABLE IF EXISTS school_types;
DROP TABLE IF EXISTS period_catalog;

SET FOREIGN_KEY_CHECKS = 1;

-- ======================================================
-- Catálogos
-- ======================================================
CREATE TABLE school_types (
    id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE shifts (
    id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE access_levels (
    id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,   -- Ej: Administrador, Profesor, Estudiante, PadreFamilia
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE period_catalog (
    id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(20) NOT NULL, -- Ej: Anual, Semestre, Trimestre
    period_number TINYINT UNSIGNED NOT NULL, -- Ej: 1, 2, 3
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Restricción para asegurar que no haya, por ejemplo, dos "Semestre" con Periodo 1.
    UNIQUE KEY uk_period_type (type_name, period_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ======================================================
-- Escuelas
-- ======================================================
CREATE TABLE schools (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    cct VARCHAR(20) NOT NULL UNIQUE,
    school_type_id TINYINT UNSIGNED NOT NULL,
    name VARCHAR(150) NOT NULL,
    postal_code CHAR(5),
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6),
    shift_id TINYINT UNSIGNED,
    period_catalog_id TINYINT UNSIGNED,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_schools_school_type FOREIGN KEY (school_type_id) REFERENCES school_types(id),
    CONSTRAINT fk_schools_shift FOREIGN KEY (shift_id) REFERENCES shifts(id),
    CONSTRAINT fk_schools_period_catalog FOREIGN KEY (period_catalog_id) REFERENCES period_catalog(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ======================================================
-- Códigos de acceso (generados por admin y referencian nivel)
-- ======================================================
CREATE TABLE access_codes (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    access_level_id TINYINT UNSIGNED NOT NULL,
    description VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by BIGINT UNSIGNED NULL, -- usuario que generó el código (puede ser admin)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_access_codes_level FOREIGN KEY (access_level_id) REFERENCES access_levels(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ======================================================
-- Usuarios (login)
-- ======================================================
CREATE TABLE users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(30),
    access_level_id TINYINT UNSIGNED NOT NULL,
    access_code_id BIGINT UNSIGNED NULL, -- referencia al código usado al registrarse (si aplica)
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_access_level FOREIGN KEY (access_level_id) REFERENCES access_levels(id),
    CONSTRAINT fk_users_access_code FOREIGN KEY (access_code_id) REFERENCES access_codes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_users_access_level ON users(access_level_id);

-- ======================================================
-- Ciclos escolares (creados por el profesor)
-- ======================================================
CREATE TABLE school_cycles (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    school_id BIGINT UNSIGNED NOT NULL,
    teacher_id BIGINT UNSIGNED NOT NULL, -- referencia a users (profesor)
    year YEAR NOT NULL,
    name VARCHAR(120),        -- ej "Ciclo 2024-2025 Grupo A"
    description TEXT,
    cycle_label VARCHAR(50),  -- ej "2024-2025"
    grade VARCHAR(20),
    group_name VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cycles_school FOREIGN KEY (school_id) REFERENCES schools(id),
    CONSTRAINT fk_cycles_teacher FOREIGN KEY (teacher_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_cycles_school_teacher ON school_cycles(school_id, teacher_id);

-- ======================================================
-- Alumnos (pertenecen a un ciclo; profesor "dueño" del alumno)
-- ======================================================
CREATE TABLE students (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    curp CHAR(18) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    birth_date DATE,
    phone VARCHAR(30),
    teacher_id BIGINT UNSIGNED NOT NULL,    -- profesor que registra / administra
    school_cycle_id BIGINT UNSIGNED NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_students_teacher FOREIGN KEY (teacher_id) REFERENCES users(id),
    CONSTRAINT fk_students_cycle FOREIGN KEY (school_cycle_id) REFERENCES school_cycles(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_students_cycle_teacher ON students(school_cycle_id, teacher_id);

-- ======================================================
-- Parciales (pertenecen a un ciclo escolar)
-- ======================================================
CREATE TABLE partials (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    school_cycle_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(80) NOT NULL,   -- ej "Parcial 1"
    start_date DATE,
    end_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_partials_cycle FOREIGN KEY (school_cycle_id) REFERENCES school_cycles(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_partials_cycle ON partials(school_cycle_id);

-- ======================================================
-- Campos formativos (por ciclo escolar)
-- ======================================================
CREATE TABLE formative_fields (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    school_cycle_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(120) NOT NULL,   -- ej "Español", "Matemáticas"
    code VARCHAR(50) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fields_cycle FOREIGN KEY (school_cycle_id) REFERENCES school_cycles(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_fields_cycle ON formative_fields(school_cycle_id);

-- ======================================================
-- Tipos de trabajo (por profesor) - p.ej Tarea, Examen
-- ======================================================
CREATE TABLE work_types (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    teacher_id BIGINT UNSIGNED NOT NULL,  -- creador/propietario del tipo
    name VARCHAR(120) NOT NULL,
    evaluation_weight DECIMAL(5,2) NOT NULL DEFAULT 0.00, -- porcentaje (ej 20.00)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_worktypes_teacher_name UNIQUE (teacher_id, name),
    CONSTRAINT fk_worktypes_teacher FOREIGN KEY (teacher_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_worktypes_teacher ON work_types(teacher_id);

-- ======================================================
-- Trabajos / Calificaciones (per alumno, por parcial, por campo formativo)
-- ======================================================
CREATE TABLE student_works (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    student_id BIGINT UNSIGNED NOT NULL,
    formative_field_id BIGINT UNSIGNED NOT NULL,
    partial_id BIGINT UNSIGNED NOT NULL,
    work_type_id BIGINT UNSIGNED NOT NULL,
    teacher_id BIGINT UNSIGNED NOT NULL, -- redundancia para consultas y seguridad (quien lo registró)
    name VARCHAR(100) NOT NULL,
    grade DECIMAL(5,2) NULL,        -- calificación del trabajo
    work_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_works_student FOREIGN KEY (student_id) REFERENCES students(id),
    CONSTRAINT fk_works_field FOREIGN KEY (formative_field_id) REFERENCES formative_fields(id),
    CONSTRAINT fk_works_partial FOREIGN KEY (partial_id) REFERENCES partials(id),
    CONSTRAINT fk_works_worktype FOREIGN KEY (work_type_id) REFERENCES work_types(id),
    CONSTRAINT fk_works_teacher FOREIGN KEY (teacher_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_works_student_partial ON student_works(student_id, partial_id);
CREATE INDEX idx_works_field_teacher ON student_works(formative_field_id, teacher_id);

-- ======================================================
-- Asistencia (por alumno y parcial)
-- ======================================================
CREATE TABLE attendances (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    student_id BIGINT UNSIGNED NOT NULL,
    partial_id BIGINT UNSIGNED NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('present','absent','late') NOT NULL DEFAULT 'present',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_attendance_student FOREIGN KEY (student_id) REFERENCES students(id),
    CONSTRAINT fk_attendance_partial FOREIGN KEY (partial_id) REFERENCES partials(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_attendance_student_date ON attendances(student_id, attendance_date);