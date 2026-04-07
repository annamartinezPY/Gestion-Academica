"""
Controlador de asistencias: registro y consulta de asistencia por sesión.
"""
from database import get_connection


def registrar_asistencia(sesion_id, estudiante_id, presente=1, observacion=""):
    """
    Registra o actualiza la asistencia de un estudiante en una sesión.
    presente=1 indica presente, 0 indica ausente.
    Retorna el id del registro o None si falla.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO asistencias (sesion_id, estudiante_id, presente, observacion)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(sesion_id, estudiante_id)
            DO UPDATE SET presente=excluded.presente, observacion=excluded.observacion
        """, (sesion_id, estudiante_id, presente, observacion))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error al registrar asistencia: {e}")
        return None
    finally:
        conn.close()


def listar_asistencia_sesion(sesion_id):
    """
    Retorna la lista de estudiantes inscritos en la cohorte de la sesión,
    con su estado de asistencia para esa sesión.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id as estudiante_id,
               u.nombre || ' ' || u.apellido as estudiante,
               u.email,
               COALESCE(a.presente, -1) as presente,
               a.observacion
        FROM sesiones s
        JOIN inscripciones i ON i.cohorte_id = s.cohorte_id AND i.estado = 'activa'
        JOIN estudiantes e ON i.estudiante_id = e.id
        JOIN usuarios u ON e.usuario_id = u.id
        LEFT JOIN asistencias a ON a.sesion_id = s.id AND a.estudiante_id = e.id
        WHERE s.id = ?
        ORDER BY u.apellido, u.nombre
    """, (sesion_id,))
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def listar_asistencia_estudiante(estudiante_id, cohorte_id=None):
    """
    Retorna el historial de asistencias de un estudiante.
    Filtra por cohorte si se indica.
    """
    conn = get_connection()
    cursor = conn.cursor()

    condiciones = ["i.estudiante_id = ?"]
    params = [estudiante_id]
    if cohorte_id:
        condiciones.append("s.cohorte_id = ?")
        params.append(cohorte_id)

    where = "WHERE " + " AND ".join(condiciones)

    cursor.execute(f"""
        SELECT s.id as sesion_id, s.fecha, s.hora_inicio, s.hora_fin, s.tema,
               co.nombre as cohorte, c.nombre as curso,
               u.nombre || ' ' || u.apellido as docente,
               COALESCE(a.presente, -1) as presente,
               a.observacion
        FROM sesiones s
        JOIN cohortes co ON s.cohorte_id = co.id
        JOIN cursos c ON co.curso_id = c.id
        JOIN docentes d ON s.docente_id = d.id
        JOIN usuarios u ON d.usuario_id = u.id
        JOIN inscripciones i ON i.cohorte_id = s.cohorte_id AND i.estudiante_id = ?
        LEFT JOIN asistencias a ON a.sesion_id = s.id AND a.estudiante_id = ?
        {where}
        ORDER BY s.fecha DESC, s.hora_inicio
    """, [estudiante_id, estudiante_id] + params)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def resumen_asistencia_cohorte(cohorte_id):
    """
    Retorna un resumen de asistencia por estudiante para una cohorte:
    total de sesiones, presentes, ausentes y porcentaje.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as total_sesiones FROM sesiones WHERE cohorte_id = ?
    """, (cohorte_id,))
    total_sesiones = cursor.fetchone()["total_sesiones"]

    cursor.execute("""
        SELECT e.id as estudiante_id,
               u.nombre || ' ' || u.apellido as estudiante,
               COUNT(a.id) as registros,
               SUM(CASE WHEN a.presente = 1 THEN 1 ELSE 0 END) as presentes,
               SUM(CASE WHEN a.presente = 0 THEN 1 ELSE 0 END) as ausentes
        FROM inscripciones i
        JOIN estudiantes e ON i.estudiante_id = e.id
        JOIN usuarios u ON e.usuario_id = u.id
        LEFT JOIN asistencias a ON a.estudiante_id = e.id
            AND a.sesion_id IN (SELECT id FROM sesiones WHERE cohorte_id = ?)
        WHERE i.cohorte_id = ? AND i.estado = 'activa'
        GROUP BY e.id
        ORDER BY u.apellido, u.nombre
    """, (cohorte_id, cohorte_id))

    estudiantes = [dict(row) for row in cursor.fetchall()]
    conn.close()

    for est in estudiantes:
        presentes = est["presentes"] or 0
        est["total_sesiones"] = total_sesiones
        est["presentes"] = presentes
        est["ausentes"] = est["ausentes"] or 0
        est["porcentaje"] = round(presentes / total_sesiones * 100, 1) if total_sesiones > 0 else 0.0

    return estudiantes
