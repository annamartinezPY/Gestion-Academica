"""
Controlador de cohortes: creación, listado, gestión de docentes asignados.
"""
from database import get_connection


def registrar_cohorte(nombre, curso_id, fecha_inicio, fecha_fin, cupo_maximo=30):
    """
    Crea una nueva cohorte para un curso.
    Retorna el id de la cohorte o None si falla.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO cohortes (nombre, curso_id, fecha_inicio, fecha_fin, cupo_maximo)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, curso_id, fecha_inicio, fecha_fin, cupo_maximo))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error al registrar cohorte: {e}")
        return None
    finally:
        conn.close()


def listar_cohortes(curso_id=None, solo_activas=True):
    """
    Retorna cohortes. Si se indica curso_id, filtra por curso.
    """
    conn = get_connection()
    cursor = conn.cursor()

    condiciones = []
    params = []
    if solo_activas:
        condiciones.append("co.activo = 1")
    if curso_id:
        condiciones.append("co.curso_id = ?")
        params.append(curso_id)

    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    cursor.execute(f"""
        SELECT co.id, co.nombre, c.nombre as curso, co.fecha_inicio,
               co.fecha_fin, co.cupo_maximo, co.activo,
               COUNT(i.id) as inscriptos
        FROM cohortes co
        JOIN cursos c ON co.curso_id = c.id
        LEFT JOIN inscripciones i ON i.cohorte_id = co.id AND i.estado = 'activa'
        {where}
        GROUP BY co.id
        ORDER BY co.fecha_inicio DESC
    """, params)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def obtener_cohorte(cohorte_id):
    """Retorna una cohorte por ID con datos del curso."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT co.id, co.nombre, co.curso_id, c.nombre as curso,
               co.fecha_inicio, co.fecha_fin, co.cupo_maximo, co.activo
        FROM cohortes co
        JOIN cursos c ON co.curso_id = c.id
        WHERE co.id = ?
    """, (cohorte_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def actualizar_cohorte(cohorte_id, nombre=None, fecha_inicio=None,
                       fecha_fin=None, cupo_maximo=None):
    """Actualiza datos de una cohorte."""
    cohorte = obtener_cohorte(cohorte_id)
    if not cohorte:
        print("Cohorte no encontrada.")
        return False

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE cohortes SET nombre=?, fecha_inicio=?, fecha_fin=?, cupo_maximo=?
            WHERE id=?
        """, (
            nombre or cohorte["nombre"],
            fecha_inicio or cohorte["fecha_inicio"],
            fecha_fin or cohorte["fecha_fin"],
            cupo_maximo if cupo_maximo is not None else cohorte["cupo_maximo"],
            cohorte_id
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar cohorte: {e}")
        return False
    finally:
        conn.close()


def registrar_sesion(cohorte_id, docente_id, fecha, hora_inicio, hora_fin, tema=""):
    """
    Registra una sesión de clase en una cohorte.
    Retorna el id de la sesión o None si falla.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO sesiones (cohorte_id, docente_id, fecha, hora_inicio, hora_fin, tema)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cohorte_id, docente_id, fecha, hora_inicio, hora_fin, tema))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error al registrar sesión: {e}")
        return None
    finally:
        conn.close()


def listar_sesiones(cohorte_id):
    """Lista todas las sesiones de una cohorte."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, s.fecha, s.hora_inicio, s.hora_fin, s.tema,
               u.nombre || ' ' || u.apellido as docente
        FROM sesiones s
        JOIN docentes d ON s.docente_id = d.id
        JOIN usuarios u ON d.usuario_id = u.id
        WHERE s.cohorte_id = ?
        ORDER BY s.fecha, s.hora_inicio
    """, (cohorte_id,))
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def cupo_disponible(cohorte_id):
    """Retorna True si la cohorte tiene cupo disponible."""
    cohorte = obtener_cohorte(cohorte_id)
    if not cohorte:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as total FROM inscripciones
        WHERE cohorte_id = ? AND estado = 'activa'
    """, (cohorte_id,))
    total = cursor.fetchone()["total"]
    conn.close()
    return total < cohorte["cupo_maximo"]


def desactivar_cohorte(cohorte_id):
    """
    Desactiva una cohorte (soft-delete: activo=0).
    Retorna True si tuvo efecto.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE cohortes SET activo = 0 WHERE id = ?", (cohorte_id,)
    )
    conn.commit()
    afectadas = cursor.rowcount
    conn.close()
    return afectadas > 0


def obtener_sesion(sesion_id):
    """Retorna una sesión por ID con datos de docente y cohorte."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, s.fecha, s.hora_inicio, s.hora_fin, s.tema,
               s.cohorte_id, s.docente_id,
               u.nombre || ' ' || u.apellido as docente,
               co.nombre as cohorte
        FROM sesiones s
        JOIN docentes d ON s.docente_id = d.id
        JOIN usuarios u ON d.usuario_id = u.id
        JOIN cohortes co ON s.cohorte_id = co.id
        WHERE s.id = ?
    """, (sesion_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def actualizar_sesion(sesion_id, docente_id=None, fecha=None,
                      hora_inicio=None, hora_fin=None, tema=None):
    """Actualiza los datos de una sesión existente."""
    sesion = obtener_sesion(sesion_id)
    if not sesion:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE sesiones
            SET docente_id=?, fecha=?, hora_inicio=?, hora_fin=?, tema=?
            WHERE id=?
        """, (
            docente_id   if docente_id   is not None else sesion["docente_id"],
            fecha        if fecha        is not None else sesion["fecha"],
            hora_inicio  if hora_inicio  is not None else sesion["hora_inicio"],
            hora_fin     if hora_fin     is not None else sesion["hora_fin"],
            tema         if tema         is not None else sesion["tema"],
            sesion_id,
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar sesión: {e}")
        return False
    finally:
        conn.close()


def eliminar_sesion(sesion_id):
    """
    Elimina una sesión y sus registros de asistencia asociados.
    Retorna True si tuvo efecto.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM asistencias WHERE sesion_id = ?", (sesion_id,))
        cursor.execute("DELETE FROM sesiones WHERE id = ?", (sesion_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al eliminar sesión: {e}")
        return False
    finally:
        conn.close()


def contar_inscriptos(cohorte_id):
    """Retorna el número de estudiantes actualmente inscriptos en una cohorte."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as total FROM inscripciones
        WHERE cohorte_id = ? AND estado = 'activa'
    """, (cohorte_id,))
    total = cursor.fetchone()["total"]
    conn.close()
    return total
