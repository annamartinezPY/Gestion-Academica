"""
Controlador de estudiantes: registro, listado, búsqueda.
"""
from database import get_connection
from controllers.usuario_controller import registrar_usuario, listar_usuarios


def registrar_estudiante(nombre, apellido, email, password, documento, telefono=""):
    """
    Crea un usuario con rol 'estudiante' y su perfil de estudiante.
    Retorna el id del estudiante o None si falla.
    """
    usuario_id = registrar_usuario(nombre, apellido, email, password, "estudiante")
    if not usuario_id:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO estudiantes (usuario_id, documento, telefono)
            VALUES (?, ?, ?)
        """, (usuario_id, documento, telefono))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            print(f"Error: ya existe un estudiante con el documento '{documento}'.")
        else:
            print(f"Error al registrar estudiante: {e}")
        return None
    finally:
        conn.close()


def listar_estudiantes():
    """Retorna todos los estudiantes con datos de usuario."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, u.nombre, u.apellido, u.email, e.documento, e.telefono, u.activo
        FROM estudiantes e
        JOIN usuarios u ON e.usuario_id = u.id
        ORDER BY u.apellido, u.nombre
    """)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def obtener_estudiante(estudiante_id):
    """Retorna un estudiante por su ID de estudiante."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, u.id as usuario_id, u.nombre, u.apellido, u.email,
               e.documento, e.telefono, u.activo
        FROM estudiantes e
        JOIN usuarios u ON e.usuario_id = u.id
        WHERE e.id = ?
    """, (estudiante_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def actualizar_estudiante(estudiante_id, documento=None, telefono=None):
    """Actualiza documento y/o teléfono de un estudiante."""
    estudiante = obtener_estudiante(estudiante_id)
    if not estudiante:
        print("Estudiante no encontrado.")
        return False

    nuevo_doc = documento or estudiante["documento"]
    nuevo_tel = telefono or estudiante["telefono"]

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE estudiantes SET documento=?, telefono=? WHERE id=?
        """, (nuevo_doc, nuevo_tel, estudiante_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar estudiante: {e}")
        return False
    finally:
        conn.close()


def buscar_estudiante_por_documento(documento):
    """Busca un estudiante por número de documento."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, u.nombre, u.apellido, u.email, e.documento, e.telefono
        FROM estudiantes e
        JOIN usuarios u ON e.usuario_id = u.id
        WHERE e.documento = ?
    """, (documento,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
