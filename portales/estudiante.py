from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from database import get_connection
from ui.helpers import console, limpiar, encabezado, ok, err, warn, mostrar_menu, pausar, pedir_int
from ui.tables import tabla_cohortes, tabla_inscripciones, tabla_pagos_estudiantes, tabla_asistencia_sesion
from controllers.cohorte_controller import listar_cohortes, obtener_cohorte, cupo_disponible
from controllers.inscripcion_controller import listar_inscripciones, inscribir_estudiante
from controllers.estudiante_controller import obtener_estudiante
from controllers.pago_controller import listar_pagos_estudiante
from controllers.asistencia_controller import listar_asistencia_estudiante
from controllers.config_controller import obtener_condiciones_curso


class PortalEstudiante:

    def __init__(self, usuario):
        self.usuario = usuario
        self.estudiante_id = self._obtener_estudiante_id()

    def _obtener_estudiante_id(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM estudiantes WHERE usuario_id = ?", (self.usuario["id"],))
        row = cursor.fetchone()
        conn.close()
        return row["id"] if row else None

    def mostrar(self):
        if not self.estudiante_id:
            err("No se encontró el perfil de estudiante.")
            pausar()
            return
        while True:
            limpiar()
            encabezado("PORTAL DEL ESTUDIANTE",
                       f"{self.usuario['nombre']} {self.usuario['apellido']}")
            op = mostrar_menu("Menú Estudiante", [
                "Mis datos", "Mis inscripciones",
                "Inscribirme en una cohorte", "Mis pagos",
                "Mi asistencia", "Cerrar sesión",
            ])
            if op == "1":
                self._mis_datos()
            elif op == "2":
                tabla_inscripciones(listar_inscripciones(estudiante_id=self.estudiante_id))
            elif op == "3":
                self._inscribirse()
            elif op == "4":
                self._mis_pagos()
            elif op == "5":
                self._mi_asistencia()
            elif op == "6":
                ok("Sesión cerrada.")
                pausar()
                break
            else:
                err("Opción inválida.")
            pausar()

    def _mis_datos(self):
        e = obtener_estudiante(self.estudiante_id)
        if not e:
            return
        console.print(Panel(
            f"[white]Nombre:[/]    [cyan]{e['nombre']} {e['apellido']}[/]\n"
            f"[white]Email:[/]     [cyan]{e['email']}[/]\n"
            f"[white]Documento:[/] [cyan]{e['documento'] or 'N/A'}[/]\n"
            f"[white]Teléfono:[/]  [cyan]{e['telefono'] or 'N/A'}[/]",
            title="[bold cyan]Mis Datos[/]", border_style="cyan", box=box.ROUNDED,
        ))

    def _inscribirse(self):
        console.print(Panel("[bold cyan]INSCRIBIRSE EN UNA COHORTE[/]", box=box.ROUNDED, border_style="cyan"))
        tabla_cohortes(listar_cohortes(solo_activas=True))
        coh_id = pedir_int("ID de cohorte")
        if coh_id is None:
            return
        cohorte = obtener_cohorte(coh_id)
        if not cohorte:
            err("Cohorte no encontrada.")
            return
        if not cupo_disponible(coh_id):
            err("Esta cohorte no tiene cupo disponible.")
            return
        condiciones = obtener_condiciones_curso(cohorte["curso_id"])
        if condiciones:
            console.print(Panel(f"[yellow]{condiciones}[/]",
                                title="[bold yellow]  Condiciones de inscripción  [/]",
                                border_style="yellow", box=box.ROUNDED))
            if not Confirm.ask("[yellow]  ¿Cumple con las condiciones de inscripción?[/]"):
                warn("Inscripción cancelada.")
                return
        console.print(
            f"\n  [white]Curso:[/] [cyan]{cohorte['curso']}[/]  |  "
            f"[white]Cohorte:[/] [cyan]{cohorte['nombre']}[/]  |  "
            f"[white]Período:[/] [cyan]{cohorte['fecha_inicio']} → {cohorte['fecha_fin']}[/]"
        )
        if Confirm.ask("[yellow]  ¿Confirma inscripción?[/]"):
            iid = inscribir_estudiante(self.estudiante_id, coh_id)
            if iid:
                ok(f"Inscripción realizada con ID {iid}.")

    def _mis_pagos(self):
        inscripciones = listar_inscripciones(estudiante_id=self.estudiante_id)
        pagos = []
        for insc in inscripciones:
            pagos.extend(listar_pagos_estudiante(inscripcion_id=insc["id"]))
        tabla_pagos_estudiantes(pagos)
        if pagos:
            total = sum(p["monto"] for p in pagos)
            console.print(f"\n  [bold cyan]Total pagado: ₲ {int(total):,}[/]".replace(",", "."))

    def _mi_asistencia(self):
        historial = listar_asistencia_estudiante(self.estudiante_id)
        if not historial:
            warn("No tenés asistencias registradas todavía.")
            return
        presentes = sum(1 for r in historial if r["presente"] == 1)
        ausentes = sum(1 for r in historial if r["presente"] == 0)
        total = len(historial)
        pct = round(presentes / total * 100, 1) if total > 0 else 0.0
        color = "green" if pct >= 75 else ("yellow" if pct >= 50 else "red")
        console.print(Panel(
            f"  [white]Total sesiones:[/]  [cyan]{total}[/]\n"
            f"  [white]Presentes:[/]       [green]{presentes}[/]\n"
            f"  [white]Ausentes:[/]        [red]{ausentes}[/]\n"
            f"  [white]Asistencia:[/]      [{color}]{pct}%[/]",
            title="[bold cyan]Mi Asistencia General[/]", border_style="cyan", box=box.ROUNDED,
        ))
        t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
        t.add_column("Fecha", min_width=12)
        t.add_column("Horario", min_width=14)
        t.add_column("Cohorte", min_width=14)
        t.add_column("Tema")
        t.add_column("Estado", justify="center", min_width=12)
        for r in historial:
            if r["presente"] == 1:
                estado = "[green]Presente[/]"
            elif r["presente"] == 0:
                estado = "[red]Ausente[/]"
            else:
                estado = "[dim]Sin registrar[/]"
            t.add_row(r["fecha"], f"{r['hora_inicio']}–{r['hora_fin']}",
                      r["cohorte"], r["tema"] or "", estado)
        console.print(t)
