"""
Controlador de inscripciones: inscribir y gestionar estudiantes en cohortes.
"""
from database import get_connection
from controllers.cohorte_controller import cupo_disponible


def inscribir_estudiante(estudiante_id, cohorte_id):
    """
    Inscribe un estudiante en una cohorte.
    Retorna el id de la inscripción o None si falla.
    """
    if not cupo_disponible(cohorte_id):
        print("Error: la cohorte no tiene cupo disponible.")
        return None

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO inscripciones (estudiante_id, cohorte_id)
            VALUES (?, ?)
        """, (estudiante_id, cohorte_id))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            print("Error: el estudiante ya está inscripto en esta cohorte.")
        else:
            print(f"Error al inscribir: {e}")
        return None
    finally:
        conn.close()


def listar_inscripciones(cohorte_id=None, estudiante_id=None):
    """Retorna inscripciones. Filtra por cohorte o estudiante si se indica."""
    conn = get_connection()
    cursor = conn.cursor()

    condiciones = []
    params = []
    if cohorte_id:
        condiciones.append("i.cohorte_id = ?")
        params.append(cohorte_id)
    if estudiante_id:
        condiciones.append("i.estudiante_id = ?")
        params.append(estudiante_id)

    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    cursor.execute(f"""
        SELECT i.id, i.estado, i.fecha_inscripcion,
               e.id as estudiante_id,
               u.nombre || ' ' || u.apellido as estudiante,
               u.email,
               co.nombre as cohorte,
               c.nombre as curso
        FROM inscripciones i
        JOIN estudiantes e ON i.estudiante_id = e.id
        JOIN usuarios u ON e.usuario_id = u.id
        JOIN cohortes co ON i.cohorte_id = co.id
        JOIN cursos c ON co.curso_id = c.id
        {where}
        ORDER BY i.fecha_inscripcion DESC
    """, params)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def obtener_inscripcion(inscripcion_id):
    """Retorna una inscripción por ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, i.estado, i.fecha_inscripcion,
               i.estudiante_id, i.cohorte_id,
               u.nombre || ' ' || u.apellido as estudiante,
               co.nombre as cohorte,
               c.nombre as curso
        FROM inscripciones i
        JOIN estudiantes e ON i.estudiante_id = e.id
        JOIN usuarios u ON e.usuario_id = u.id
        JOIN cohortes co ON i.cohorte_id = co.id
        JOIN cursos c ON co.curso_id = c.id
        WHERE i.id = ?
    """, (inscripcion_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def cancelar_inscripcion(inscripcion_id):
    """Cancela una inscripción (cambia estado a 'cancelada')."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE inscripciones SET estado='cancelada' WHERE id=?",
        (inscripcion_id,)
    )
    conn.commit()
    afectadas = cursor.rowcount
    conn.close()
    return afectadas > 0


def reactivar_inscripcion(inscripcion_id):
    """
    Reactiva una inscripción cancelada (vuelve a estado 'activa').
    Verifica que haya cupo disponible antes de reactivar.
    Retorna True si tuvo efecto, False si no hay cupo o no se encontró.
    """
    inscripcion = obtener_inscripcion(inscripcion_id)
    if not inscripcion:
        return False, "Inscripción no encontrada."
    if inscripcion["estado"] == "activa":
        return False, "La inscripción ya está activa."

    if not cupo_disponible(inscripcion["cohorte_id"]):
        return False, "No hay cupo disponible en la cohorte."

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE inscripciones SET estado='activa' WHERE id=?",
        (inscripcion_id,)
    )
    conn.commit()
    afectadas = cursor.rowcount
    conn.close()
    return (True, "Inscripción reactivada.") if afectadas > 0 else (False, "Error al reactivar.")


def listar_inscripciones_pendientes_pago():
    """
    Retorna inscripciones activas que no tienen ningún pago registrado.
    Útil para identificar estudiantes con deuda.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, i.fecha_inscripcion,
               e.id as estudiante_id,
               u.nombre || ' ' || u.apellido as estudiante,
               u.email,
               co.nombre as cohorte,
               c.nombre as curso,
               c.tarifa_estudiante
        FROM inscripciones i
        JOIN estudiantes e ON i.estudiante_id = e.id
        JOIN usuarios u ON e.usuario_id = u.id
        JOIN cohortes co ON i.cohorte_id = co.id
        JOIN cursos c ON co.curso_id = c.id
        WHERE i.estado = 'activa'
          AND NOT EXISTS (
              SELECT 1 FROM pagos_estudiantes pe WHERE pe.inscripcion_id = i.id
          )
        ORDER BY i.fecha_inscripcion ASC
    """)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def contar_inscriptos_cohorte(cohorte_id):
    """Retorna la cantidad de inscriptos activos en una cohorte."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as total FROM inscripciones
        WHERE cohorte_id = ? AND estado = 'activa'
    """, (cohorte_id,))
    total = cursor.fetchone()["total"]
    conn.close()
    return total
