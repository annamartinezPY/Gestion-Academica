"""
Módulo de configuración y conexión a la base de datos SQLite.
"""
import sqlite3
import os

DB_NAME = "gestion_academica.db"


def get_connection():
    """Retorna una conexión a la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
    conn.execute("PRAGMA foreign_keys = ON")  # Activa claves foráneas
    return conn


def inicializar_db():
    """Crea todas las tablas si no existen."""
    conn = get_connection()
    cursor = conn.cursor()

    # --- Tabla de roles (parametrizable) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT
        )
    """)

    # --- Tabla de usuarios ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            rol_id INTEGER NOT NULL,
            activo INTEGER DEFAULT 1,
            fecha_creacion TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (rol_id) REFERENCES roles(id)
        )
    """)

    # --- Tabla de modalidades (parametrizable) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modalidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT
        )
    """)

    # --- Tabla de cursos ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            modalidad_id INTEGER NOT NULL,
            horas_totales INTEGER DEFAULT 0,
            tarifa_estudiante REAL DEFAULT 0.0,
            activo INTEGER DEFAULT 1,
            FOREIGN KEY (modalidad_id) REFERENCES modalidades(id)
        )
    """)

    # --- Tabla de cohortes ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cohortes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            curso_id INTEGER NOT NULL,
            fecha_inicio TEXT NOT NULL,
            fecha_fin TEXT NOT NULL,
            cupo_maximo INTEGER DEFAULT 30,
            activo INTEGER DEFAULT 1,
            FOREIGN KEY (curso_id) REFERENCES cursos(id)
        )
    """)

    # --- Tabla de docentes ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS docentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL UNIQUE,
            especialidad TEXT,
            tarifa_hora REAL DEFAULT 0.0,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    # --- Tabla de estudiantes ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL UNIQUE,
            documento TEXT UNIQUE,
            telefono TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    # --- Tabla de inscripciones ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inscripciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id INTEGER NOT NULL,
            cohorte_id INTEGER NOT NULL,
            fecha_inscripcion TEXT DEFAULT (datetime('now')),
            estado TEXT DEFAULT 'activa',
            UNIQUE(estudiante_id, cohorte_id),
            FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id),
            FOREIGN KEY (cohorte_id) REFERENCES cohortes(id)
        )
    """)

    # --- Tabla de sesiones de clase ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sesiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cohorte_id INTEGER NOT NULL,
            docente_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            hora_inicio TEXT NOT NULL,
            hora_fin TEXT NOT NULL,
            tema TEXT,
            FOREIGN KEY (cohorte_id) REFERENCES cohortes(id),
            FOREIGN KEY (docente_id) REFERENCES docentes(id)
        )
    """)

    # --- Tabla de pagos de estudiantes ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos_estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inscripcion_id INTEGER NOT NULL,
            monto REAL NOT NULL,
            fecha_pago TEXT DEFAULT (datetime('now')),
            metodo_pago TEXT DEFAULT 'efectivo',
            estado TEXT DEFAULT 'pagado',
            observacion TEXT,
            FOREIGN KEY (inscripcion_id) REFERENCES inscripciones(id)
        )
    """)

    # --- Tabla de pagos a docentes ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos_docentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            docente_id INTEGER NOT NULL,
            cohorte_id INTEGER NOT NULL,
            horas_dictadas REAL NOT NULL,
            monto REAL NOT NULL,
            fecha_pago TEXT DEFAULT (datetime('now')),
            estado TEXT DEFAULT 'pendiente',
            observacion TEXT,
            FOREIGN KEY (docente_id) REFERENCES docentes(id),
            FOREIGN KEY (cohorte_id) REFERENCES cohortes(id)
        )
    """)

    # --- Tabla de asistencias ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asistencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sesion_id INTEGER NOT NULL,
            estudiante_id INTEGER NOT NULL,
            presente INTEGER DEFAULT 1,
            observacion TEXT,
            UNIQUE(sesion_id, estudiante_id),
            FOREIGN KEY (sesion_id) REFERENCES sesiones(id),
            FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id)
        )
    """)

    # --- Tabla de configuración del sistema (parametrizable) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL,
            descripcion TEXT,
            tipo TEXT DEFAULT 'texto'
        )
    """)

    # --- Datos iniciales (seeds) ---
    _insertar_datos_iniciales(cursor)
    _insertar_configuracion_inicial(cursor)

    # --- Migraciones (añade columnas si no existen) ---
    _aplicar_migraciones(cursor)

    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")


def _insertar_datos_iniciales(cursor):
    """Inserta datos de configuración iniciales si no existen."""
    # Roles
    roles = [
        ("admin", "Administrador del sistema"),
        ("docente", "Docente del instituto"),
        ("estudiante", "Estudiante inscripto"),
    ]
    for nombre, desc in roles:
        cursor.execute(
            "INSERT OR IGNORE INTO roles (nombre, descripcion) VALUES (?, ?)",
            (nombre, desc)
        )

    # Modalidades
    modalidades = [
        ("presencial", "Clases en aula física"),
        ("virtual", "Clases en línea / videoconferencia"),
        ("hibrida", "Combinación de presencial y virtual"),
    ]
    for nombre, desc in modalidades:
        cursor.execute(
            "INSERT OR IGNORE INTO modalidades (nombre, descripcion) VALUES (?, ?)",
            (nombre, desc)
        )


def _aplicar_migraciones(cursor):
    """Añade columnas nuevas a tablas existentes sin romper datos previos."""

    def _tiene_columna(tabla, columna):
        cursor.execute(f"PRAGMA table_info({tabla})")
        return any(row["name"] == columna for row in cursor.fetchall())

    # pagos_docentes: tipo de pago y concepto de materiales
    if not _tiene_columna("pagos_docentes", "tipo_pago"):
        cursor.execute(
            "ALTER TABLE pagos_docentes ADD COLUMN tipo_pago TEXT DEFAULT 'horas'"
        )
    if not _tiene_columna("pagos_docentes", "concepto"):
        cursor.execute(
            "ALTER TABLE pagos_docentes ADD COLUMN concepto TEXT"
        )

    # cursos: condiciones de ingreso (texto libre parametrizable)
    if not _tiene_columna("cursos", "condiciones_ingreso"):
        cursor.execute(
            "ALTER TABLE cursos ADD COLUMN condiciones_ingreso TEXT"
        )


def _insertar_configuracion_inicial(cursor):
    """Inserta configuración de sistema por defecto."""
    defaults = [
        ("porcentaje_asistencia_minima", "75",
         "% de asistencia mínima requerida para aprobar", "numero"),
        ("moneda", "USD",
         "Moneda del sistema (USD, ARS, EUR…)", "texto"),
        ("nombre_instituto", "Instituto de Formación",
         "Nombre del instituto que aparece en reportes", "texto"),
        ("cupo_maximo_default", "30",
         "Cupo máximo por defecto para nuevas cohortes", "numero"),
        ("dias_cancelacion_inscripcion", "7",
         "Días máximos para cancelar una inscripción sin penalidad", "numero"),
    ]
    for clave, valor, desc, tipo in defaults:
        cursor.execute(
            "INSERT OR IGNORE INTO configuracion (clave, valor, descripcion, tipo) VALUES (?,?,?,?)",
            (clave, valor, desc, tipo),
        )


if __name__ == "__main__":
    inicializar_db()
