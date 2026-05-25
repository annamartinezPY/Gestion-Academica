from database import get_connection


def listar_instituciones(solo_activas=False):
    conn = get_connection()
    query = """
        SELECT i.*,
               GROUP_CONCAT(m.nombre, ', ') AS modalidades
        FROM instituciones i
        LEFT JOIN institucion_modalidades im ON im.institucion_id = i.id
        LEFT JOIN modalidades m ON m.id = im.modalidad_id
        {}
        GROUP BY i.id
        ORDER BY i.nombre
    """.format("WHERE i.activo = 1" if solo_activas else "")
    rows = conn.execute(query).fetchall()
    conn.close()
    return rows


def obtener_institucion(institucion_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM instituciones WHERE id = ?", (institucion_id,)
    ).fetchone()
    conn.close()
    return row


def registrar_institucion(nombre, email="", telefono=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO instituciones (nombre, email, telefono) VALUES (?, ?, ?)",
        (nombre, email, telefono),
    )
    conn.commit()
    institucion_id = cursor.lastrowid
    conn.close()
    return institucion_id


def actualizar_institucion(institucion_id, nombre, email="", telefono=""):
    conn = get_connection()
    conn.execute(
        "UPDATE instituciones SET nombre=?, email=?, telefono=? WHERE id=?",
        (nombre, email, telefono, institucion_id),
    )
    conn.commit()
    conn.close()


def desactivar_institucion(institucion_id):
    conn = get_connection()
    conn.execute(
        "UPDATE instituciones SET activo=0 WHERE id=?", (institucion_id,)
    )
    conn.commit()
    conn.close()


# ── Modalidades de la institución ──────────────────────────────────────────

def listar_modalidades_institucion(institucion_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT m.id, m.nombre, m.descripcion
        FROM modalidades m
        JOIN institucion_modalidades im ON im.modalidad_id = m.id
        WHERE im.institucion_id = ?
        ORDER BY m.nombre
    """, (institucion_id,)).fetchall()
    conn.close()
    return rows


def agregar_modalidad_institucion(institucion_id, modalidad_id):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO institucion_modalidades (institucion_id, modalidad_id) VALUES (?, ?)",
            (institucion_id, modalidad_id),
        )
        conn.commit()
        return True, "Modalidad agregada."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def quitar_modalidad_institucion(institucion_id, modalidad_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM institucion_modalidades WHERE institucion_id=? AND modalidad_id=?",
        (institucion_id, modalidad_id),
    )
    conn.commit()
    conn.close()


# ── Cursos de la institución ────────────────────────────────────────────────

def listar_cursos_institucion(institucion_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.*, m.nombre AS modalidad_nombre,
               COUNT(co.id) AS total_cohortes
        FROM cursos c
        JOIN modalidades m ON m.id = c.modalidad_id
        LEFT JOIN cohortes co ON co.curso_id = c.id
        WHERE c.institucion_id = ?
        GROUP BY c.id
        ORDER BY c.nombre
    """, (institucion_id,)).fetchall()
    conn.close()
    return rows


def asignar_institucion_curso(curso_id, institucion_id):
    conn = get_connection()
    conn.execute(
        "UPDATE cursos SET institucion_id=? WHERE id=?",
        (institucion_id, curso_id),
    )
    conn.commit()
    conn.close()
