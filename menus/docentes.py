from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from ui.helpers import console, limpiar, encabezado, ok, err, mostrar_menu, pausar, pedir_int, pedir_float, pedir_email
from ui.tables import tabla_docentes
from controllers.docente_controller import (
    registrar_docente, listar_docentes, obtener_docente,
    actualizar_docente, desactivar_docente,
    listar_cohortes_docente, buscar_docente_por_email,
)


class MenuDocentes:

    def mostrar(self):
        while True:
            limpiar()
            encabezado("GESTIÓN DE DOCENTES")
            op = mostrar_menu("Docentes", [
                "Listar docentes", "Registrar docente", "Actualizar docente",
                "Ver cohortes de un docente", "Buscar docente por email",
                "Desactivar docente", "Volver",
            ])
            if op == "1":
                tabla_docentes(listar_docentes())
            elif op == "2":
                self._registrar()
            elif op == "3":
                self._actualizar()
            elif op == "4":
                self._cohortes()
            elif op == "5":
                self._buscar()
            elif op == "6":
                self._desactivar()
            elif op == "7":
                break
            else:
                err("Opción inválida.")
            pausar()

    def _registrar(self):
        console.print(Panel("[bold cyan]REGISTRAR DOCENTE[/]", box=box.ROUNDED, border_style="cyan"))
        nombre = Prompt.ask("[white]  Nombre[/]").strip()
        apellido = Prompt.ask("[white]  Apellido[/]").strip()
        email = pedir_email("Email")
        password = Prompt.ask("[white]  Contraseña[/]", password=True).strip()
        especialidad = Prompt.ask("[white]  Especialidad (opcional)[/]", default="").strip()
        tarifa = pedir_float("Tarifa por hora (₲)", 0.0)
        did = registrar_docente(nombre, apellido, email, password, especialidad, tarifa)
        if did:
            ok(f"Docente registrado con ID {did}.")

    def _actualizar(self):
        tabla_docentes(listar_docentes())
        did = pedir_int("ID a actualizar")
        if did is None:
            return
        d = obtener_docente(did)
        if not d:
            err("Docente no encontrado.")
            return
        console.print(f"  [dim]Editando: {d['nombre']} {d['apellido']}[/]")
        especialidad = Prompt.ask(
            f"[white]  Especialidad (Enter = [dim]{d['especialidad'] or 'vacía'}[/])[/]", default=""
        ).strip() or None
        tarifa_str = Prompt.ask(
            f"[white]  Tarifa/hora ₲ (Enter = [dim]{int(d['tarifa_hora']):,}[/])[/]", default=""
        ).strip()
        tarifa = float(tarifa_str) if tarifa_str else None
        if actualizar_docente(did, especialidad, tarifa):
            ok("Docente actualizado.")

    def _cohortes(self):
        tabla_docentes(listar_docentes())
        did = pedir_int("ID de docente")
        if did is None:
            return
        d = obtener_docente(did)
        if not d:
            err("Docente no encontrado.")
            return
        cohortes = listar_cohortes_docente(did)
        if not cohortes:
            from ui.helpers import warn
            warn(f"{d['nombre']} {d['apellido']} no tiene sesiones registradas.")
            return
        encabezado(f"Cohortes de {d['nombre']} {d['apellido']}")
        t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
        t.add_column("ID", width=5)
        t.add_column("Cohorte", min_width=15)
        t.add_column("Curso", min_width=20)
        t.add_column("Inicio", min_width=12)
        t.add_column("Fin", min_width=12)
        t.add_column("Sesiones", justify="right", width=9)
        t.add_column("Horas dict.", justify="right", width=11)
        for co in cohortes:
            t.add_row(
                str(co["id"]), co["cohorte"], co["curso"],
                co["fecha_inicio"], co["fecha_fin"],
                str(co["total_sesiones"]),
                f"[cyan]{co['horas_totales'] or 0:.1f}h[/]",
            )
        console.print(t)

    def _buscar(self):
        email = pedir_email("Email del docente")
        d = buscar_docente_por_email(email)
        if d:
            console.print(Panel(
                f"[white]ID:[/] [cyan]{d['id']}[/]   "
                f"[white]Nombre:[/] [cyan]{d['nombre']} {d['apellido']}[/]\n"
                f"[white]Especialidad:[/] [cyan]{d['especialidad'] or 'N/A'}[/]   "
                f"[white]Tarifa:[/] [cyan]₲ {int(d['tarifa_hora']):,}/h[/]   ".replace(",", ".")
                + f"[white]Activo:[/] {'[green]Sí[/]' if d['activo'] else '[red]No[/]'}",
                title="[green]Docente encontrado[/]", border_style="green", box=box.ROUNDED,
            ))
        else:
            err("No se encontró ningún docente con ese email.")

    def _desactivar(self):
        tabla_docentes(listar_docentes())
        did = pedir_int("ID a desactivar")
        if did is None:
            return
        d = obtener_docente(did)
        if not d:
            err("Docente no encontrado.")
            return
        if Confirm.ask(f"[yellow]  ¿Confirma desactivar a {d['nombre']} {d['apellido']}?[/]"):
            ok("Desactivado.") if desactivar_docente(did) else err("No se pudo desactivar.")
