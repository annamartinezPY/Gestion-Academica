from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from ui.helpers import console, limpiar, encabezado, ok, err, warn, mostrar_menu, pausar, pedir_int
from ui.tables import tabla_cohortes, tabla_estudiantes, tabla_inscripciones
from controllers.cohorte_controller import listar_cohortes, obtener_cohorte, cupo_disponible
from controllers.inscripcion_controller import (
    inscribir_estudiante, listar_inscripciones, obtener_inscripcion,
    cancelar_inscripcion, reactivar_inscripcion, listar_inscripciones_pendientes_pago,
)
from controllers.estudiante_controller import listar_estudiantes
from controllers.config_controller import obtener_condiciones_curso


class MenuInscripciones:

    def mostrar(self):
        while True:
            limpiar()
            encabezado("GESTIÓN DE INSCRIPCIONES")
            op = mostrar_menu("Inscripciones", [
                "Ver inscripciones de una cohorte",
                "Ver inscripciones de un estudiante",
                "Inscribir estudiante en cohorte",
                "Cancelar inscripción",
                "Reactivar inscripción cancelada",
                "Ver inscripciones sin pago registrado",
                "Volver",
            ])
            if op == "1":
                self._por_cohorte()
            elif op == "2":
                self._por_estudiante()
            elif op == "3":
                self._inscribir()
            elif op == "4":
                self._cancelar()
            elif op == "5":
                self._reactivar()
            elif op == "6":
                self._sin_pago()
            elif op == "7":
                break
            else:
                err("Opción inválida.")
            pausar()

    def _por_cohorte(self):
        tabla_cohortes(listar_cohortes(solo_activas=False))
        cohorte_id = pedir_int("ID de cohorte")
        if not cohorte_id:
            return
        inscripciones = listar_inscripciones(cohorte_id=cohorte_id)
        tabla_inscripciones(inscripciones)
        if inscripciones:
            activas = sum(1 for i in inscripciones if i["estado"] == "activa")
            canceladas = sum(1 for i in inscripciones if i["estado"] == "cancelada")
            console.print(
                f"  [dim]Total: {len(inscripciones)}  |  "
                f"[green]Activas: {activas}[/]  |  [red]Canceladas: {canceladas}[/][/]"
            )

    def _por_estudiante(self):
        tabla_estudiantes(listar_estudiantes())
        est_id = pedir_int("ID de estudiante")
        if not est_id:
            return
        tabla_inscripciones(listar_inscripciones(estudiante_id=est_id))

    def _inscribir(self):
        console.print(Panel("[bold cyan]INSCRIBIR ESTUDIANTE[/]", box=box.ROUNDED, border_style="cyan"))
        tabla_estudiantes(listar_estudiantes())
        est_id = pedir_int("ID de estudiante")
        if est_id is None:
            return
        tabla_cohortes(listar_cohortes(solo_activas=True))
        coh_id = pedir_int("ID de cohorte")
        if coh_id is None:
            return
        cohorte = obtener_cohorte(coh_id)
        if not cohorte:
            err("Cohorte no encontrada.")
            return
        condiciones = obtener_condiciones_curso(cohorte["curso_id"])
        if condiciones:
            console.print(Panel(f"[yellow]{condiciones}[/]",
                                title="[bold yellow]  Condiciones de inscripción  [/]",
                                border_style="yellow", box=box.ROUNDED))
        if not cupo_disponible(coh_id):
            err("La cohorte no tiene cupo disponible.")
            return
        iid = inscribir_estudiante(est_id, coh_id)
        if iid:
            ok(f"Inscripción registrada con ID {iid}.")
        else:
            err("No se pudo inscribir. El estudiante puede ya estar inscripto en esta cohorte.")

    def _cancelar(self):
        tabla_cohortes(listar_cohortes(solo_activas=False))
        cohorte_id = pedir_int("ID de cohorte")
        if cohorte_id is None:
            return
        tabla_inscripciones(listar_inscripciones(cohorte_id=cohorte_id))
        iid = pedir_int("ID de inscripción a cancelar")
        if iid is None:
            return
        insc = obtener_inscripcion(iid)
        if not insc:
            err("Inscripción no encontrada.")
            return
        if insc["estado"] == "cancelada":
            warn("Esta inscripción ya está cancelada.")
            return
        if Confirm.ask(f"[yellow]  ¿Confirma cancelar inscripción de '{insc['estudiante']}'?[/]"):
            ok("Cancelada.") if cancelar_inscripcion(iid) else err("Error al cancelar.")

    def _reactivar(self):
        console.print(Panel("[bold cyan]REACTIVAR INSCRIPCIÓN[/]", box=box.ROUNDED, border_style="cyan"))
        tabla_cohortes(listar_cohortes(solo_activas=False))
        cohorte_id = pedir_int("ID de cohorte")
        if cohorte_id is None:
            return
        todas = listar_inscripciones(cohorte_id=cohorte_id)
        canceladas = [i for i in todas if i["estado"] == "cancelada"]
        if not canceladas:
            warn("No hay inscripciones canceladas en esta cohorte.")
            return
        tabla_inscripciones(canceladas)
        iid = pedir_int("ID de inscripción a reactivar")
        if iid is None:
            return
        exito, mensaje = reactivar_inscripcion(iid)
        ok(mensaje) if exito else err(mensaje)

    def _sin_pago(self):
        pendientes = listar_inscripciones_pendientes_pago()
        if not pendientes:
            ok("Todos los estudiantes inscriptos tienen al menos un pago registrado.")
            return
        encabezado("INSCRIPCIONES SIN PAGO REGISTRADO")
        t = Table(box=box.ROUNDED, border_style="yellow", header_style="bold yellow")
        t.add_column("Insc.ID", style="dim", width=8)
        t.add_column("Estudiante", min_width=24)
        t.add_column("Email", min_width=22)
        t.add_column("Cohorte", min_width=15)
        t.add_column("Curso", min_width=18)
        t.add_column("Tarifa", justify="right", min_width=14)
        t.add_column("Fecha inscr.", min_width=13)
        for p in pendientes:
            tarifa = f"[yellow]₲ {int(p['tarifa_estudiante']):,}[/]".replace(",", ".")
            t.add_row(str(p["id"]), p["estudiante"], p["email"],
                      p["cohorte"], p["curso"], tarifa, p["fecha_inscripcion"][:10])
        console.print(t)
        console.print(f"\n  [bold yellow]  ⚠  {len(pendientes)} estudiante(s) sin pago registrado[/]")
