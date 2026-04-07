"""
Controlador de docentes: registro, listado, actualización.
"""
from database import get_connection
from controllers.usuario_controller import registrar_usuario


def registrar_docente(nombre, apellido, email, password, especialidad="", tarifa_hora=0.0):
    """
    Crea un usuario con rol 'docente' y su perfil de docente.
    Retorna el id del docente o None si falla.
    """
    usuario_id = registrar_usuario(nombre, apellido, email, password, "docente")
    if not usuario_id:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO docentes (usuario_id, especialidad, tarifa_hora)
            VALUES (?, ?, ?)
        """, (usuario_id, especialidad, tarifa_hora))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error al registrar docente: {e}")
        return None
    finally:
        conn.close()


def listar_docentes():
    """Retorna todos los docentes con datos de usuario."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.id, u.nombre, u.apellido, u.email,
               d.especialidad, d.tarifa_hora, u.activo
        FROM docentes d
        JOIN usuarios u ON d.usuario_id = u.id
        ORDER BY u.apellido, u.nombre
    """)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def obtener_docente(docente_id):
    """Retorna un docente por su ID de docente."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.id, u.id as usuario_id, u.nombre, u.apellido, u.email,
               d.especialidad, d.tarifa_hora, u.activo
        FROM docentes d
        JOIN usuarios u ON d.usuario_id = u.id
        WHERE d.id = ?
    """, (docente_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def actualizar_docente(docente_id, especialidad=None, tarifa_hora=None):
    """Actualiza especialidad y/o tarifa de un docente."""
    docente = obtener_docente(docente_id)
    if not docente:
        print("Docente no encontrado.")
        return False

    nueva_esp = especialidad if especialidad is not None else docente["especialidad"]
    nueva_tarifa = tarifa_hora if tarifa_hora is not None else docente["tarifa_hora"]

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE docentes SET especialidad=?, tarifa_hora=? WHERE id=?
        """, (nueva_esp, nueva_tarifa, docente_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar docente: {e}")
        return False
    finally:
        conn.close()


def calcular_pago_docente(docente_id, horas_dictadas):
    """
    Calcula el monto a pagar a un docente según su tarifa por hora.
    Retorna el monto calculado.
    """
    docente = obtener_docente(docente_id)
    if not docente:
        return 0.0
    return docente["tarifa_hora"] * horas_dictadas


def desactivar_docente(docente_id):
    """
    Desactiva el usuario asociado al docente (soft-delete).
    Retorna True si tuvo efecto.
    """
    docente = obtener_docente(docente_id)
    if not docente:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE usuarios SET activo = 0 WHERE id = ?", (docente["usuario_id"],)
    )
    conn.commit()
    afectadas = cursor.rowcount
    conn.close()
    return afectadas > 0


def listar_cohortes_docente(docente_id):
    """
    Retorna las cohortes en las que el docente tiene al menos una sesión registrada,
    junto con el total de horas dictadas y sesiones.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT co.id, co.nombre as cohorte, c.nombre as curso,
               co.fecha_inicio, co.fecha_fin,
               COUNT(s.id) as total_sesiones,
               ROUND(
                   SUM(
                       (CAST(substr(s.hora_fin,1,2) AS REAL) + CAST(substr(s.hora_fin,4,2) AS REAL)/60)
                     - (CAST(substr(s.hora_inicio,1,2) AS REAL) + CAST(substr(s.hora_inicio,4,2) AS REAL)/60)
                   ), 2
               ) as horas_totales
        FROM sesiones s
        JOIN cohortes co ON s.cohorte_id = co.id
        JOIN cursos c ON co.curso_id = c.id
        WHERE s.docente_id = ?
        GROUP BY co.id
        ORDER BY co.fecha_inicio DESC
    """, (docente_id,))
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def buscar_docente_por_email(email):
    """Retorna un docente buscando por email de usuario."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.id, u.id as usuario_id, u.nombre, u.apellido, u.email,
               d.especialidad, d.tarifa_hora, u.activo
        FROM docentes d
        JOIN usuarios u ON d.usuario_id = u.id
        WHERE u.email = ?
    """, (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
