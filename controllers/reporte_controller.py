"""
Controlador de reportes: genera reportes académicos y administrativos.
"""
from database import get_connection


# ──────────────────────────────────────────────
#  Reportes académicos
# ──────────────────────────────────────────────

def reporte_cursos():
    """
    Reporte de cursos con cantidad de cohortes e inscriptos totales.
    Incluye todos los cursos (activos e inactivos).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.nombre as curso, m.nombre as modalidad,
               c.horas_totales, c.tarifa_estudiante,
               c.activo,
               COUNT(DISTINCT co.id) as total_cohortes,
               COUNT(DISTINCT i.id) as total_inscriptos
        FROM cursos c
        JOIN modalidades m ON c.modalidad_id = m.id
        LEFT JOIN cohortes co ON co.curso_id = c.id
        LEFT JOIN inscripciones i ON i.cohorte_id = co.id AND i.estado = 'activa'
        GROUP BY c.id
        ORDER BY total_inscriptos DESC, c.nombre
    """)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def reporte_cohortes(solo_activas=False):
    """
    Reporte de cohortes con ocupación, ingresos y estado de asistencia.
    """
    conn = get_connection()
    cursor = conn.cursor()
    where = "WHERE co.activo = 1" if solo_activas else ""
    cursor.execute(f"""
        SELECT co.id, co.nombre as cohorte, c.nombre as curso,
               m.nombre as modalidad,
               co.fecha_inicio, co.fecha_fin, co.cupo_maximo,
               COUNT(DISTINCT i.id) as inscriptos,
               COALESCE(SUM(pe.monto), 0) as ingresos_estudiantes,
               COALESCE((
                   SELECT SUM(pd.monto) FROM pagos_docentes pd WHERE pd.cohorte_id = co.id
               ), 0) as pagos_docentes,
               COUNT(DISTINCT s.id) as total_sesiones
        FROM cohortes co
        JOIN cursos c ON co.curso_id = c.id
        JOIN modalidades m ON c.modalidad_id = m.id
        LEFT JOIN inscripciones i ON i.cohorte_id = co.id AND i.estado = 'activa'
        LEFT JOIN pagos_estudiantes pe ON pe.inscripcion_id = i.id
        LEFT JOIN sesiones s ON s.cohorte_id = co.id
        {where}
        GROUP BY co.id
        ORDER BY co.fecha_inicio DESC
    """)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    for r in result:
        r["ocupacion_pct"] = (
            round(r["inscriptos"] / r["cupo_maximo"] * 100, 1)
            if r["cupo_maximo"] > 0 else 0.0
        )
        r["balance"] = r["ingresos_estudiantes"] - r["pagos_docentes"]
    return result


def reporte_participacion_cohorte(cohorte_id):
    """
    Reporte académico detallado de una cohorte:
    por estudiante: inscripción, asistencia y pagos.
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
               u.email,
               i.estado as estado_inscripcion,
               i.fecha_inscripcion,
               COALESCE(SUM(CASE WHEN a.presente = 1 THEN 1 ELSE 0 END), 0) as presentes,
               COALESCE(SUM(pe.monto), 0) as total_pagado
        FROM inscripciones i
        JOIN estudiantes e ON i.estudiante_id = e.id
        JOIN usuarios u ON e.usuario_id = u.id
        LEFT JOIN asistencias a ON a.estudiante_id = e.id
            AND a.sesion_id IN (SELECT id FROM sesiones WHERE cohorte_id = ?)
        LEFT JOIN pagos_estudiantes pe ON pe.inscripcion_id = i.id
        WHERE i.cohorte_id = ?
        GROUP BY e.id
        ORDER BY u.apellido, u.nombre
    """, (cohorte_id, cohorte_id))
    estudiantes = [dict(row) for row in cursor.fetchall()]
    conn.close()

    for e in estudiantes:
        e["total_sesiones"] = total_sesiones
        e["pct_asistencia"] = (
            round(e["presentes"] / total_sesiones * 100, 1)
            if total_sesiones > 0 else 0.0
        )
        e["aprobado"] = e["pct_asistencia"] >= 75.0
    return estudiantes


def reporte_docentes():
    """
    Reporte de actividad de docentes: cohortes asignadas, horas dictadas y pagos recibidos.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.id, u.nombre || ' ' || u.apellido as docente,
               u.email, d.especialidad, d.tarifa_hora,
               COUNT(DISTINCT s.cohorte_id) as cohortes_asignadas,
               COALESCE(SUM(s_horas.duracion_h), 0) as horas_dictadas_sesiones,
               COALESCE(SUM(pd.monto), 0) as total_cobrado
        FROM docentes d
        JOIN usuarios u ON d.usuario_id = u.id
        LEFT JOIN sesiones s ON s.docente_id = d.id
        LEFT JOIN (
            SELECT docente_id,
                   SUM(
                       (CAST(substr(hora_fin,1,2) AS REAL) + CAST(substr(hora_fin,4,2) AS REAL)/60)
                     - (CAST(substr(hora_inicio,1,2) AS REAL) + CAST(substr(hora_inicio,4,2) AS REAL)/60)
                   ) as duracion_h
            FROM sesiones
            GROUP BY docente_id
        ) s_horas ON s_horas.docente_id = d.id
        LEFT JOIN pagos_docentes pd ON pd.docente_id = d.id AND pd.estado = 'pagado'
        GROUP BY d.id
        ORDER BY total_cobrado DESC
    """)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


# ──────────────────────────────────────────────
#  Reportes administrativos / financieros
# ──────────────────────────────────────────────

def reporte_financiero_global():
    """
    Resumen financiero global del sistema:
    ingresos totales (estudiantes), egresos (docentes), balance.
    Desglosado por modalidad y tipo de pago.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Ingresos por modalidad
    cursor.execute("""
        SELECT m.nombre as modalidad,
               COUNT(DISTINCT pe.id) as cantidad_pagos,
               COALESCE(SUM(pe.monto), 0) as total
        FROM pagos_estudiantes pe
        JOIN inscripciones i ON pe.inscripcion_id = i.id
        JOIN cohortes co ON i.cohorte_id = co.id
        JOIN cursos c ON co.curso_id = c.id
        JOIN modalidades m ON c.modalidad_id = m.id
        GROUP BY m.id
        ORDER BY total DESC
    """)
    ingresos_modalidad = [dict(r) for r in cursor.fetchall()]

    # Egresos por tipo de pago
    cursor.execute("""
        SELECT COALESCE(tipo_pago, 'horas') as tipo,
               COUNT(*) as cantidad_pagos,
               COALESCE(SUM(monto), 0) as total
        FROM pagos_docentes
        GROUP BY tipo_pago
    """)
    egresos_tipo = [dict(r) for r in cursor.fetchall()]

    # Totales generales
    cursor.execute("SELECT COALESCE(SUM(monto), 0) as total FROM pagos_estudiantes")
    total_ingresos = cursor.fetchone()["total"]

    cursor.execute("SELECT COALESCE(SUM(monto), 0) as total FROM pagos_docentes")
    total_egresos = cursor.fetchone()["total"]

    # Pagos pendientes de docentes
    cursor.execute("""
        SELECT COALESCE(SUM(monto), 0) as total FROM pagos_docentes WHERE estado = 'pendiente'
    """)
    pagos_pendientes = cursor.fetchone()["total"]

    conn.close()
    return {
        "total_ingresos": total_ingresos,
        "total_egresos": total_egresos,
        "balance": total_ingresos - total_egresos,
        "pagos_pendientes_docentes": pagos_pendientes,
        "ingresos_por_modalidad": ingresos_modalidad,
        "egresos_por_tipo": egresos_tipo,
    }


def reporte_inscripciones_periodo(anio=None):
    """
    Reporte de inscripciones agrupadas por mes y curso.
    Si se indica año, filtra por ese año.
    """
    conn = get_connection()
    cursor = conn.cursor()
    where = f"AND strftime('%Y', i.fecha_inscripcion) = '{anio}'" if anio else ""
    cursor.execute(f"""
        SELECT strftime('%Y-%m', i.fecha_inscripcion) as mes,
               c.nombre as curso,
               m.nombre as modalidad,
               COUNT(*) as inscriptos,
               SUM(CASE WHEN i.estado = 'cancelada' THEN 1 ELSE 0 END) as canceladas
        FROM inscripciones i
        JOIN cohortes co ON i.cohorte_id = co.id
        JOIN cursos c ON co.curso_id = c.id
        JOIN modalidades m ON c.modalidad_id = m.id
        WHERE 1=1 {where}
        GROUP BY mes, c.id
        ORDER BY mes DESC, inscriptos DESC
    """)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result
