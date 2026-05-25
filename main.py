"""
Plataforma de Gestión Académica — Punto de entrada.
Ejecutar: python main.py
"""
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box

from database import inicializar_db, get_connection
from controllers.usuario_controller import login, registrar_usuario
from ui.helpers import console, limpiar, encabezado, ok, warn, mostrar_menu, pausar, pedir_email
from rich.prompt import Prompt
from portales.admin import PortalAdmin
from portales.docente import PortalDocente
from portales.estudiante import PortalEstudiante


def _crear_admin_inicial():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE email = 'admin@sistema.com'")
    existe = cursor.fetchone()
    conn.close()
    if not existe:
        uid = registrar_usuario("Admin", "Sistema", "admin@sistema.com", "admin123", "admin")
        if uid:
            console.print("[dim]  Admin creado: admin@sistema.com / admin123[/]")


def _pantalla_login():
    limpiar()
    encabezado("PLATAFORMA DE GESTIÓN ACADÉMICA", "Sistema de administración educativa")
    console.print()
    console.print(Panel("[bold cyan]  INICIAR SESIÓN  [/]", box=box.ROUNDED, border_style="cyan", width=52))
    email = Prompt.ask("[white]  Email[/]").strip()
    password = Prompt.ask("[white]  Contraseña[/]", password=True).strip()
    usuario = login(email, password)
    if usuario:
        ok(f"Bienvenido/a, {usuario['nombre']} {usuario['apellido']}  [{usuario['rol'].upper()}]")
        pausar()
        return usuario
    from ui.helpers import err
    err("Credenciales incorrectas o usuario inactivo.")
    pausar()
    return None


def main():
    inicializar_db()
    _crear_admin_inicial()

    portales = {
        "admin":      PortalAdmin,
        "docente":    PortalDocente,
        "estudiante": PortalEstudiante,
    }

    while True:
        limpiar()
        encabezado("PLATAFORMA DE GESTIÓN ACADÉMICA", "Sistema de administración educativa")
        op = mostrar_menu("Menú Principal", ["Iniciar sesión", "Salir"])
        if op == "1":
            usuario = _pantalla_login()
            if usuario:
                rol = usuario["rol"]
                if rol in portales:
                    portales[rol](usuario).mostrar()
                else:
                    warn(f"Módulo para rol '{rol}' no disponible.")
                    pausar()
        elif op == "2":
            limpiar()
            console.print(Panel(
                Align.center(Text("¡Hasta luego!", style="bold cyan")),
                box=box.ROUNDED, border_style="cyan", width=40, padding=(1, 0),
            ))
            console.print()
            break
        else:
            from ui.helpers import err
            err("Opción inválida.")
            pausar()


if __name__ == "__main__":
    main()
