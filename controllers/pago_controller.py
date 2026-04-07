"""
Controlador de pagos: pagos de estudiantes y pagos a docentes.
"""
from database import get_connection
from controllers.docente_controller import calcular_pago_docente


def registrar_pago_estudiante(inscripcion_id, monto, metodo_pago="efectivo", observacion=""):
    """
    Registra un pago de un estudiante.
    Retorna el id del pago o None si falla.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO pagos_estudiantes (inscripcion_id, monto, metodo_pago, observacion)
            VALUES (?, ?, ?, ?)
        """, (inscripcion_id, monto, metodo_pago, observacion))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error al registrar pago: {e}")
        return None
    finally:
        conn.close()


def listar_pagos_estudiante(inscripcion_id=None, estudiante_id=None):
    """Lista pagos de estudiantes. Filtra por inscripción o estudiante."""
    conn = get_connection()
    cursor = conn.cursor()

    condiciones = []
    params = []
    if inscripcion_id:
        condiciones.append("pe.inscripcion_id = ?")
        params.append(inscripcion_id)
    if estudiante_id:
        condiciones.append("e.id = ?")
        params.append(estudiante_id)

    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    cursor.execute(f"""
        SELECT pe.id, pe.monto, pe.fecha_pago, pe.metodo_pago, pe.estado, pe.observacion,
               u.nombre || ' ' || u.apellido as estudiante,
               co.nombre as cohorte,
               c.nombre as curso
        FROM pagos_estudiantes pe
        JOIN inscripciones i ON pe.inscripcion_id = i.id
        JOIN estudiantes e ON i.estudiante_id = e.id
        JOIN usuarios u ON e.usuario_id = u.id
        JOIN cohortes co ON i.cohorte_id = co.id
        JOIN cursos c ON co.curso_id = c.id
        {where}
        ORDER BY pe.fecha_pago DESC
    """, params)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def registrar_pago_docente(docente_id, cohorte_id, horas_dictadas, observacion=""):
    """
    Registra un pago a un docente calculado por horas dictadas.
    Retorna el id del pago o None si falla.
    """
    monto = calcular_pago_docente(docente_id, horas_dictadas)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO pagos_docentes
                (docente_id, cohorte_id, horas_dictadas, monto, observacion, tipo_pago)
            VALUES (?, ?, ?, ?, ?, 'horas')
        """, (docente_id, cohorte_id, horas_dictadas, monto, observacion))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error al registrar pago docente: {e}")
        return None
    finally:
        conn.close()


def registrar_pago_materiales_docente(docente_id, cohorte_id, monto, concepto, observacion=""):
    """
    Registra un pago a un docente por materiales utilizados en el curso.
    El monto se ingresa directamente (no se calcula por tarifa/hora).
    Retorna el id del pago o None si falla.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO pagos_docentes
                (docente_id, cohorte_id, horas_dictadas, monto, observacion, tipo_pago, concepto)
            VALUES (?, ?, 0, ?, ?, 'materiales', ?)
        """, (docente_id, cohorte_id, monto, observacion, concepto))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error al registrar pago por materiales: {e}")
        return None
    finally:
        conn.close()


def listar_pagos_docente(docente_id=None, cohorte_id=None):
    """Lista pagos a docentes. Filtra por docente o cohorte."""
    conn = get_connection()
    cursor = conn.cursor()

    condiciones = []
    params = []
    if docente_id:
        condiciones.append("pd.docente_id = ?")
        params.append(docente_id)
    if cohorte_id:
        condiciones.append("pd.cohorte_id = ?")
        params.append(cohorte_id)

    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    cursor.execute(f"""
        SELECT pd.id, pd.horas_dictadas, pd.monto, pd.fecha_pago, pd.estado, pd.observacion,
               COALESCE(pd.tipo_pago, 'horas') as tipo_pago,
               pd.concepto,
               u.nombre || ' ' || u.apellido as docente,
               co.nombre as cohorte,
               c.nombre as curso
        FROM pagos_docentes pd
        JOIN docentes d ON pd.docente_id = d.id
        JOIN usuarios u ON d.usuario_id = u.id
        JOIN cohortes co ON pd.cohorte_id = co.id
        JOIN cursos c ON co.curso_id = c.id
        {where}
        ORDER BY pd.fecha_pago DESC
    """, params)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def anular_pago_estudiante(pago_id):
    """
    Anula un pago de estudiante cambiando su estado a 'anulado'.
    Retorna True si tuvo efecto.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pagos_estudiantes SET estado='anulado' WHERE id=?", (pago_id,)
    )
    conn.commit()
    afectadas = cursor.rowcount
    conn.close()
    return afectadas > 0


def listar_pagos_cohorte(cohorte_id):
    """
    Lista todos los pagos de estudiantes de una cohorte completa.
    Incluye estado del pago y monto de la tarifa del curso.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pe.id, pe.monto, pe.fecha_pago, pe.metodo_pago, pe.estado, pe.observacion,
               u.nombre || ' ' || u.apellido as estudiante,
               u.email,
               co.nombre as cohorte,
               c.nombre as curso,
               c.tarifa_estudiante
        FROM pagos_estudiantes pe
        JOIN inscripciones i ON pe.inscripcion_id = i.id
        JOIN estudiantes e ON i.estudiante_id = e.id
        JOIN usuarios u ON e.usuario_id = u.id
        JOIN cohortes co ON i.cohorte_id = co.id
        JOIN cursos c ON co.curso_id = c.id
        WHERE i.cohorte_id = ?
        ORDER BY pe.fecha_pago DESC
    """, (cohorte_id,))
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def marcar_pago_docente_pagado(pago_id):
    """
    Cambia el estado de un pago a docente de 'pendiente' a 'pagado'.
    Retorna True si tuvo efecto.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pagos_docentes SET estado='pagado' WHERE id=? AND estado='pendiente'",
        (pago_id,)
    )
    conn.commit()
    afectadas = cursor.rowcount
    conn.close()
    return afectadas > 0


def anular_pago_docente(pago_id):
    """
    Anula un pago a docente cambiando su estado a 'anulado'.
    Retorna True si tuvo efecto.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pagos_docentes SET estado='anulado' WHERE id=?", (pago_id,)
    )
    conn.commit()
    afectadas = cursor.rowcount
    conn.close()
    return afectadas > 0


def listar_pagos_docente_pendientes():
    """Lista todos los pagos a docentes con estado 'pendiente'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pd.id, pd.horas_dictadas, pd.monto, pd.fecha_pago, pd.estado, pd.observacion,
               COALESCE(pd.tipo_pago, 'horas') as tipo_pago,
               pd.concepto,
               u.nombre || ' ' || u.apellido as docente,
               co.nombre as cohorte,
               c.nombre as curso
        FROM pagos_docentes pd
        JOIN docentes d ON pd.docente_id = d.id
        JOIN usuarios u ON d.usuario_id = u.id
        JOIN cohortes co ON pd.cohorte_id = co.id
        JOIN cursos c ON co.curso_id = c.id
        WHERE pd.estado = 'pendiente'
        ORDER BY pd.fecha_pago ASC
    """)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def resumen_pagos_cohorte(cohorte_id):
    """
    Retorna un resumen financiero para una cohorte:
    total recaudado de estudiantes y total pagado a docentes.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(pe.monto), 0) as total_estudiantes
        FROM pagos_estudiantes pe
        JOIN inscripciones i ON pe.inscripcion_id = i.id
        WHERE i.cohorte_id = ?
    """, (cohorte_id,))
    total_est = cursor.fetchone()["total_estudiantes"]

    cursor.execute("""
        SELECT COALESCE(SUM(monto), 0) as total_docentes
        FROM pagos_docentes
        WHERE cohorte_id = ?
    """, (cohorte_id,))
    total_doc = cursor.fetchone()["total_docentes"]
    conn.close()
    return {
        "total_estudiantes": total_est,
        "total_docentes": total_doc,
        "balance": total_est - total_doc
    }
