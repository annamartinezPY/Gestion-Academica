"""
Controlador de usuarios: registro, login, listado, edición.
"""
import hashlib
from database import get_connection


def _hash_password(password: str) -> str:
    """Hashea la contraseña con SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def registrar_usuario(nombre, apellido, email, password, rol_nombre):
    """
    Registra un nuevo usuario en el sistema.
    Retorna el id del usuario creado o None si ya existe el email.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Buscar rol
        cursor.execute("SELECT id FROM roles WHERE nombre = ?", (rol_nombre,))
        rol = cursor.fetchone()
        if not rol:
            print(f"Error: el rol '{rol_nombre}' no existe.")
            return None

        hashed = _hash_password(password)
        cursor.execute("""
            INSERT INTO usuarios (nombre, apellido, email, password, rol_id)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, apellido, email, hashed, rol["id"]))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            print(f"Error: ya existe un usuario con el email '{email}'.")
        else:
            print(f"Error al registrar usuario: {e}")
        return None
    finally:
        conn.close()


def login(email, password):
    """
    Verifica credenciales. Retorna el usuario (dict) o None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    hashed = _hash_password(password)
    cursor.execute("""
        SELECT u.id, u.nombre, u.apellido, u.email, r.nombre as rol
        FROM usuarios u
        JOIN roles r ON u.rol_id = r.id
        WHERE u.email = ? AND u.password = ? AND u.activo = 1
    """, (email, hashed))
    usuario = cursor.fetchone()
    conn.close()
    if usuario:
        return dict(usuario)
    return None


def listar_usuarios():
    """Retorna todos los usuarios activos con su rol."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.nombre, u.apellido, u.email, r.nombre as rol, u.activo
        FROM usuarios u
        JOIN roles r ON u.rol_id = r.id
        ORDER BY u.apellido, u.nombre
    """)
    usuarios = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return usuarios


def obtener_usuario(usuario_id):
    """Retorna un usuario por ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.nombre, u.apellido, u.email, r.nombre as rol, u.activo
        FROM usuarios u
        JOIN roles r ON u.rol_id = r.id
        WHERE u.id = ?
    """, (usuario_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def actualizar_usuario(usuario_id, nombre=None, apellido=None, email=None):
    """Actualiza datos básicos de un usuario."""
    conn = get_connection()
    cursor = conn.cursor()
    usuario = obtener_usuario(usuario_id)
    if not usuario:
        print("Usuario no encontrado.")
        conn.close()
        return False

    nuevo_nombre = nombre or usuario["nombre"]
    nuevo_apellido = apellido or usuario["apellido"]
    nuevo_email = email or usuario["email"]

    try:
        cursor.execute("""
            UPDATE usuarios SET nombre=?, apellido=?, email=?
            WHERE id=?
        """, (nuevo_nombre, nuevo_apellido, nuevo_email, usuario_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar: {e}")
        return False
    finally:
        conn.close()


def desactivar_usuario(usuario_id):
    """Desactiva (borra lógicamente) un usuario."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET activo=0 WHERE id=?", (usuario_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0
