from rich.panel import Panel
from rich.prompt import Prompt
from rich import box
from ui.helpers import console, limpiar, encabezado, ok, err, mostrar_menu, pausar, pedir_int, pedir_email, pedir_telefono
from ui.tables import tabla_estudiantes
from controllers.estudiante_controller import (
    registrar_estudiante, listar_estudiantes,
    actualizar_estudiante, buscar_estudiante_por_documento,
)


class MenuEstudiantes:

    def mostrar(self):
        while True:
            limpiar()
            encabezado("GESTIÓN DE ESTUDIANTES")
            op = mostrar_menu("Estudiantes", [
                "Listar estudiantes", "Registrar estudiante",
                "Buscar por documento", "Actualizar estudiante", "Volver",
            ])
            if op == "1":
                tabla_estudiantes(listar_estudiantes())
            elif op == "2":
                self._registrar()
            elif op == "3":
                self._buscar()
            elif op == "4":
                self._actualizar()
            elif op == "5":
                break
            else:
                err("Opción inválida.")
            pausar()

    def _registrar(self):
        console.print(Panel("[bold cyan]REGISTRAR ESTUDIANTE[/]", box=box.ROUNDED, border_style="cyan"))
        nombre = Prompt.ask("[white]  Nombre[/]").strip()
        apellido = Prompt.ask("[white]  Apellido[/]").strip()
        email = pedir_email("Email")
        password = Prompt.ask("[white]  Contraseña[/]", password=True).strip()
        documento = Prompt.ask("[white]  Documento (CI/Pasaporte)[/]").strip()
        telefono = pedir_telefono("Teléfono (opcional)")
        eid = registrar_estudiante(nombre, apellido, email, password, documento, telefono)
        if eid:
            ok(f"Estudiante registrado con ID {eid}.")

    def _buscar(self):
        doc = Prompt.ask("[white]  Número de documento[/]").strip()
        e = buscar_estudiante_por_documento(doc)
        if e:
            console.print(Panel(
                f"[white]ID:[/] [cyan]{e['id']}[/]   "
                f"[white]Nombre:[/] [cyan]{e['nombre']} {e['apellido']}[/]   "
                f"[white]Email:[/] [cyan]{e['email']}[/]",
                title="[green]Estudiante encontrado[/]",
                border_style="green", box=box.ROUNDED,
            ))
        else:
            err("No se encontró ningún estudiante con ese documento.")

    def _actualizar(self):
        tabla_estudiantes(listar_estudiantes())
        eid = pedir_int("ID a actualizar")
        if eid is None:
            return
        documento = Prompt.ask("[white]  Nuevo documento (Enter = sin cambio)[/]", default="").strip() or None
        telefono = pedir_telefono("Nuevo teléfono (Enter = sin cambio)") or None
        if actualizar_estudiante(eid, documento, telefono):
            ok("Estudiante actualizado.")
