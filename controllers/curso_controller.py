"""
Controlador de cursos: creación, listado, actualización.
"""
from database import get_connection


def listar_modalidades():
    """Retorna todas las modalidades disponibles."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, descripcion FROM modalidades")
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def registrar_curso(nombre, descripcion, modalidad_id, horas_totales, tarifa_estudiante):
    """
    Crea un nuevo curso.
    Retorna el id del curso creado o None si falla.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO cursos (nombre, descripcion, modalidad_id, horas_totales, tarifa_estudiante)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, descripcion, modalidad_id, horas_totales, tarifa_estudiante))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error al registrar curso: {e}")
        return None
    finally:
        conn.close()


def listar_cursos(solo_activos=True):
    """Retorna cursos con su modalidad."""
    conn = get_connection()
    cursor = conn.cursor()
    filtro = "WHERE c.activo = 1" if solo_activos else ""
    cursor.execute(f"""
        SELECT c.id, c.nombre, c.descripcion, m.nombre as modalidad,
               c.horas_totales, c.tarifa_estudiante, c.activo
        FROM cursos c
        JOIN modalidades m ON c.modalidad_id = m.id
        {filtro}
        ORDER BY c.nombre
    """)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def obtener_curso(curso_id):
    """Retorna un curso por ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.nombre, c.descripcion, m.id as modalidad_id,
               m.nombre as modalidad, c.horas_totales, c.tarifa_estudiante, c.activo
        FROM cursos c
        JOIN modalidades m ON c.modalidad_id = m.id
        WHERE c.id = ?
    """, (curso_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def actualizar_curso(curso_id, nombre=None, descripcion=None,
                     modalidad_id=None, horas_totales=None, tarifa_estudiante=None):
    """Actualiza datos de un curso."""
    curso = obtener_curso(curso_id)
    if not curso:
        print("Curso no encontrado.")
        return False

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE cursos SET
                nombre=?, descripcion=?, modalidad_id=?,
                horas_totales=?, tarifa_estudiante=?
            WHERE id=?
        """, (
            nombre or curso["nombre"],
            descripcion or curso["descripcion"],
            modalidad_id or curso["modalidad_id"],
            horas_totales if horas_totales is not None else curso["horas_totales"],
            tarifa_estudiante if tarifa_estudiante is not None else curso["tarifa_estudiante"],
            curso_id
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar curso: {e}")
        return False
    finally:
        conn.close()


def desactivar_curso(curso_id):
    """Desactiva un curso."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE cursos SET activo=0 WHERE id=?", (curso_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0
