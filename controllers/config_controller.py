"""
Controlador de configuración: parámetros parametrizables del sistema.
"""
from database import get_connection


# ──────────────────────────────────────────────
#  Configuración general del sistema
# ──────────────────────────────────────────────

def obtener_config(clave):
    """Retorna el valor de un parámetro de configuración."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
    row = cursor.fetchone()
    conn.close()
    return row["valor"] if row else None


def listar_config():
    """Retorna todas las configuraciones del sistema."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT clave, valor, descripcion, tipo FROM configuracion ORDER BY clave")
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def actualizar_config(clave, valor):
    """Actualiza el valor de un parámetro existente. Retorna True si tuvo efecto."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE configuracion SET valor = ? WHERE clave = ?", (valor, clave)
    )
    conn.commit()
    afectadas = cursor.rowcount
    conn.close()
    return afectadas > 0


# ──────────────────────────────────────────────
#  Modalidades de cursado (parametrizable)
# ──────────────────────────────────────────────

def listar_modalidades():
    """Retorna todas las modalidades."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, descripcion FROM modalidades ORDER BY nombre")
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def agregar_modalidad(nombre, descripcion=""):
    """
    Agrega una nueva modalidad de cursado.
    Retorna el id o None si ya existe.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO modalidades (nombre, descripcion) VALUES (?, ?)",
            (nombre.strip(), descripcion.strip()),
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            return None
        print(f"Error al agregar modalidad: {e}")
        return None
    finally:
        conn.close()


def actualizar_modalidad(modalidad_id, nombre=None, descripcion=None):
    """Actualiza nombre o descripción de una modalidad."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, descripcion FROM modalidades WHERE id = ?", (modalidad_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    try:
        cursor.execute(
            "UPDATE modalidades SET nombre = ?, descripcion = ? WHERE id = ?",
            (nombre or row["nombre"], descripcion if descripcion is not None else row["descripcion"], modalidad_id),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar modalidad: {e}")
        return False
    finally:
        conn.close()


# ──────────────────────────────────────────────
#  Roles de usuario (parametrizable)
# ──────────────────────────────────────────────

def listar_roles():
    """Retorna todos los roles del sistema."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, descripcion FROM roles ORDER BY id")
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def agregar_rol(nombre, descripcion=""):
    """
    Agrega un nuevo rol de usuario.
    Retorna el id o None si ya existe.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO roles (nombre, descripcion) VALUES (?, ?)",
            (nombre.strip().lower(), descripcion.strip()),
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            return None
        print(f"Error al agregar rol: {e}")
        return None
    finally:
        conn.close()


# ──────────────────────────────────────────────
#  Condiciones de inscripción por curso
# ──────────────────────────────────────────────

def obtener_condiciones_curso(curso_id):
    """Retorna las condiciones de ingreso de un curso."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT condiciones_ingreso FROM cursos WHERE id = ?", (curso_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row["condiciones_ingreso"] if row else None


def actualizar_condiciones_curso(curso_id, condiciones):
    """Define/actualiza las condiciones de inscripción para un curso."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE cursos SET condiciones_ingreso = ? WHERE id = ?",
        (condiciones.strip() if condiciones else None, curso_id),
    )
    conn.commit()
    afectadas = cursor.rowcount
    conn.close()
    return afectadas > 0
