from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box
from ui.helpers import console, limpiar, encabezado, ok, err, warn, mostrar_menu, pausar, pedir_int, exportar_csv
from ui.tables import tabla_cohortes, tabla_sesiones, tabla_estudiantes, tabla_asistencia_sesion, tabla_resumen_asistencia
from controllers.cohorte_controller import listar_cohortes, obtener_cohorte, listar_sesiones
from controllers.estudiante_controller import listar_estudiantes
from controllers.asistencia_controller import (
    registrar_asistencia, listar_asistencia_sesion,
    listar_asistencia_estudiante, resumen_asistencia_cohorte,
)


class MenuAsistencias:

    def mostrar(self):
        while True:
            limpiar()
            encabezado("GESTIÓN DE ASISTENCIAS")
            op = mostrar_menu("Asistencias", [
                "Registrar asistencia de una sesión",
                "Ver asistencia de una sesión",
                "Resumen de asistencia de una cohorte",
                "Historial de asistencia de un estudiante",
                "Exportar resumen a CSV",
                "Volver",
            ])
            if op == "1":
                self._registrar()
            elif op == "2":
                self._ver_sesion()
            elif op == "3":
                self._resumen_cohorte()
            elif op == "4":
                self._historial_estudiante()
            elif op == "5":
                self._exportar_csv()
            elif op == "6":
                break
            else:
                err("Opción inválida.")
            pausar()

    def _seleccionar_sesion(self):
        tabla_cohortes(listar_cohortes(solo_activas=False))
        cohorte_id = pedir_int("ID de cohorte")
        if cohorte_id is None:
            return None, None
        sesiones = listar_sesiones(cohorte_id)
        tabla_sesiones(sesiones)
        sesion_id = pedir_int("ID de sesión")
        return sesion_id, cohorte_id

    def _registrar(self):
        console.print(Panel("[bold cyan]REGISTRAR ASISTENCIA[/]", box=box.ROUNDED, border_style="cyan"))
        sesion_id, _ = self._seleccionar_sesion()
        if sesion_id is None:
            return
        registros = listar_asistencia_sesion(sesion_id)
        if not registros:
            warn("No hay estudiantes inscriptos en esta cohorte.")
            return
        tabla_asistencia_sesion(registros)
        console.print("\n  [dim]Para cada estudiante, indique [green]P[/]=Presente / [red]A[/]=Ausente / Enter=omitir[/]")
        cambios = 0
        for r in registros:
            resp = Prompt.ask(
                f"  [cyan]{r['estudiante']}[/]",
                choices=["P", "p", "A", "a", ""], default="", show_choices=False,
            ).strip().upper()
            if resp == "P":
                registrar_asistencia(sesion_id, r["estudiante_id"], presente=1)
                cambios += 1
            elif resp == "A":
                registrar_asistencia(sesion_id, r["estudiante_id"], presente=0)
                cambios += 1
        ok(f"Asistencia guardada. {cambios} registro(s) actualizados.")

    def _ver_sesion(self):
        sesion_id, _ = self._seleccionar_sesion()
        if sesion_id is None:
            return
        tabla_asistencia_sesion(listar_asistencia_sesion(sesion_id))

    def _resumen_cohorte(self):
        tabla_cohortes(listar_cohortes(solo_activas=False))
        cohorte_id = pedir_int("ID de cohorte")
        if cohorte_id is None:
            return
        cohorte = obtener_cohorte(cohorte_id)
        if not cohorte:
            err("Cohorte no encontrada.")
            return
        encabezado(f"Asistencia: {cohorte['nombre']} — {cohorte['curso']}")
        tabla_resumen_asistencia(resumen_asistencia_cohorte(cohorte_id))

    def _historial_estudiante(self):
        tabla_estudiantes(listar_estudiantes())
        est_id = pedir_int("ID de estudiante")
        if est_id is None:
            return
        historial = listar_asistencia_estudiante(est_id)
        if not historial:
            warn("Sin historial de asistencias.")
            return
        t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
        t.add_column("Fecha", min_width=12)
        t.add_column("Horario", min_width=14)
        t.add_column("Cohorte", min_width=14)
        t.add_column("Tema")
        t.add_column("Asistencia", justify="center", min_width=12)
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

    def _exportar_csv(self):
        tabla_cohortes(listar_cohortes(solo_activas=False))
        cohorte_id = pedir_int("ID de cohorte")
        if cohorte_id is None:
            return
        cohorte = obtener_cohorte(cohorte_id)
        if not cohorte:
            err("Cohorte no encontrada.")
            return
        resumen = resumen_asistencia_cohorte(cohorte_id)
        nombre = f"asistencia_{cohorte['nombre'].replace(' ', '_')}.csv"
        exportar_csv(resumen, nombre)
