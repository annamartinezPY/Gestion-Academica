from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box
from ui.helpers import console, limpiar, encabezado, ok, err, mostrar_menu, pausar, pedir_int, pedir_email
from ui.tables import tabla_usuarios
from controllers.usuario_controller import (
    registrar_usuario, listar_usuarios, actualizar_usuario, desactivar_usuario,
)


class MenuUsuarios:

    def mostrar(self):
        while True:
            limpiar()
            encabezado("GESTIÓN DE USUARIOS")
            op = mostrar_menu("Usuarios", [
                "Listar usuarios", "Registrar usuario",
                "Actualizar usuario", "Desactivar usuario", "Volver",
            ])
            if op == "1":
                tabla_usuarios(listar_usuarios())
            elif op == "2":
                self._registrar()
            elif op == "3":
                self._actualizar()
            elif op == "4":
                self._desactivar()
            elif op == "5":
                break
            else:
                err("Opción inválida.")
            pausar()

    def _registrar(self):
        console.print(Panel("[bold cyan]REGISTRAR USUARIO[/]", box=box.ROUNDED, border_style="cyan"))
        nombre = Prompt.ask("[white]  Nombre[/]").strip()
        apellido = Prompt.ask("[white]  Apellido[/]").strip()
        email = pedir_email("Email")
        password = Prompt.ask("[white]  Contraseña[/]", password=True).strip()
        console.print("  Roles: [cyan]admin[/], [cyan]docente[/], [cyan]estudiante[/]")
        rol = Prompt.ask("[white]  Rol[/]").strip().lower()
        uid = registrar_usuario(nombre, apellido, email, password, rol)
        if uid:
            ok(f"Usuario registrado con ID {uid}.")

    def _actualizar(self):
        tabla_usuarios(listar_usuarios())
        uid = pedir_int("ID a actualizar")
        if uid is None:
            return
        nombre = Prompt.ask("[white]  Nuevo nombre (Enter = sin cambio)[/]", default="").strip() or None
        apellido = Prompt.ask("[white]  Nuevo apellido (Enter = sin cambio)[/]", default="").strip() or None
        email = pedir_email("Nuevo email (Enter = sin cambio)", requerido=False) or None
        if actualizar_usuario(uid, nombre, apellido, email):
            ok("Usuario actualizado.")

    def _desactivar(self):
        tabla_usuarios(listar_usuarios())
        uid = pedir_int("ID a desactivar")
        if uid is None:
            return
        if Confirm.ask(f"[yellow]  ¿Confirma desactivar usuario {uid}?[/]"):
            ok("Desactivado.") if desactivar_usuario(uid) else err("No encontrado.")
