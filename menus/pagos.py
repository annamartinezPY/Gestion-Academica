from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from ui.helpers import console, limpiar, encabezado, ok, err, warn, mostrar_menu, pausar, pedir_int, pedir_float
from ui.tables import tabla_cohortes, tabla_docentes, tabla_estudiantes, tabla_inscripciones, tabla_pagos_estudiantes, tabla_pagos_docentes
from controllers.cohorte_controller import listar_cohortes, obtener_cohorte
from controllers.docente_controller import listar_docentes, obtener_docente
from controllers.estudiante_controller import listar_estudiantes
from controllers.inscripcion_controller import listar_inscripciones
from controllers.pago_controller import (
    registrar_pago_estudiante, listar_pagos_estudiante, anular_pago_estudiante, listar_pagos_cohorte,
    registrar_pago_docente, registrar_pago_materiales_docente,
    listar_pagos_docente, listar_pagos_docente_pendientes,
    marcar_pago_docente_pagado, anular_pago_docente, resumen_pagos_cohorte,
)


class MenuPagos:

    def mostrar(self):
        while True:
            limpiar()
            encabezado("GESTIÓN DE PAGOS")
            op = mostrar_menu("Pagos", [
                "── ESTUDIANTES ──",
                "Registrar pago de estudiante",
                "Ver pagos de una cohorte",
                "Ver pagos de un estudiante",
                "Anular pago de estudiante",
                "── DOCENTES ──",
                "Registrar pago a docente (por horas)",
                "Registrar pago a docente (por materiales)",
                "Ver pagos a docentes",
                "Ver pagos pendientes de docentes",
                "Marcar pago docente como pagado",
                "Anular pago a docente",
                "── RESUMEN ──",
                "Resumen financiero de cohorte",
                "Volver",
            ])
            if op == "2":
                self._pago_estudiante()
            elif op == "3":
                self._pagos_cohorte()
            elif op == "4":
                self._pagos_estudiante()
            elif op == "5":
                self._anular_estudiante()
            elif op == "7":
                self._pago_docente_horas()
            elif op == "8":
                self._pago_docente_materiales()
            elif op == "9":
                tabla_pagos_docentes(listar_pagos_docente())
            elif op == "10":
                self._pendientes_docentes()
            elif op == "11":
                self._marcar_pagado_docente()
            elif op == "12":
                self._anular_docente()
            elif op == "14":
                self._resumen_cohorte()
            elif op == "15":
                break
            elif op in ("1", "6", "13"):
                pass  # separadores
            else:
                err("Opción inválida.")
            pausar()

    def _pago_estudiante(self):
        console.print(Panel("[bold cyan]REGISTRAR PAGO DE ESTUDIANTE[/]", box=box.ROUNDED, border_style="cyan"))
        tabla_cohortes(listar_cohortes(solo_activas=False))
        cohorte_id = pedir_int("ID de cohorte")
        if cohorte_id is None:
            return
        tabla_inscripciones(listar_inscripciones(cohorte_id=cohorte_id))
        insc_id = pedir_int("ID de inscripción")
        if insc_id is None:
            return
        monto = pedir_float("Monto (₲)")
        console.print("  Métodos: [cyan]efectivo[/], [cyan]transferencia[/]")
        metodo = Prompt.ask("[white]  Método de pago[/]", default="efectivo").strip()
        obs = Prompt.ask("[white]  Observación (opcional)[/]", default="").strip()
        pid = registrar_pago_estudiante(insc_id, monto, metodo, obs)
        if pid:
            ok(f"Pago registrado con ID {pid}. Monto: ₲ {int(monto):,}".replace(",", "."))

    def _pagos_cohorte(self):
        tabla_cohortes(listar_cohortes(solo_activas=False))
        coh_id = pedir_int("ID de cohorte")
        if coh_id is None:
            return
        pagos = listar_pagos_cohorte(coh_id)
        tabla_pagos_estudiantes(pagos)
        if pagos:
            total = sum(p["monto"] for p in pagos if p["estado"] != "anulado")
            anulados = sum(1 for p in pagos if p["estado"] == "anulado")
            console.print(
                f"  [dim]Total cobrado: [green]₲ {int(total):,}[/]".replace(",", ".")
                + (f"  |  Anulados: [red]{anulados}[/]" if anulados else "") + "[/]"
            )

    def _pagos_estudiante(self):
        tabla_estudiantes(listar_estudiantes())
        est_id = pedir_int("ID de estudiante")
        if est_id is None:
            return
        pagos = listar_pagos_estudiante(estudiante_id=est_id)
        tabla_pagos_estudiantes(pagos)
        if pagos:
            total = sum(p["monto"] for p in pagos if p["estado"] != "anulado")
            console.print(f"  [dim]Total pagado: [green]₲ {int(total):,}[/][/]".replace(",", "."))

    def _anular_estudiante(self):
        tabla_cohortes(listar_cohortes(solo_activas=False))
        coh_id = pedir_int("ID de cohorte")
        if coh_id is None:
            return
        pagos = listar_pagos_cohorte(coh_id)
        tabla_pagos_estudiantes(pagos)
        if not pagos:
            return
        pid = pedir_int("ID de pago a anular")
        if pid is None:
            return
        pago = next((p for p in pagos if p["id"] == pid), None)
        if not pago:
            err("Pago no encontrado en esta cohorte.")
            return
        if pago["estado"] == "anulado":
            warn("Este pago ya está anulado.")
            return
        monto_str = f"₲ {int(pago['monto']):,}".replace(",", ".")
        if Confirm.ask(f"[yellow]  ¿Confirma anular pago {monto_str} de '{pago['estudiante']}'?[/]"):
            ok("Pago anulado.") if anular_pago_estudiante(pid) else err("Error al anular.")

    def _pago_docente_horas(self):
        console.print(Panel("[bold cyan]REGISTRAR PAGO A DOCENTE[/]", box=box.ROUNDED, border_style="cyan"))
        tabla_docentes(listar_docentes())
        did = pedir_int("ID de docente")
        if did is None:
            return
        tabla_cohortes(listar_cohortes(solo_activas=False))
        coh_id = pedir_int("ID de cohorte")
        if coh_id is None:
            return
        horas = pedir_float("Horas dictadas")
        docente = obtener_docente(did)
        monto_calc = docente["tarifa_hora"] * horas if docente else 0
        console.print(
            f"  [cyan]Monto calculado: ₲ {int(monto_calc):,}[/]  "
            f"(tarifa [white]₲ {int(docente['tarifa_hora']):,}[/]/h × [white]{horas}[/]h)".replace(",", ".")
        )
        obs = Prompt.ask("[white]  Observación (opcional)[/]", default="").strip()
        pid = registrar_pago_docente(did, coh_id, horas, obs)
        if pid:
            ok(f"Pago registrado con ID {pid}.")

    def _pago_docente_materiales(self):
        console.print(Panel("[bold cyan]REGISTRAR PAGO POR MATERIALES — DOCENTE[/]", box=box.ROUNDED, border_style="cyan"))
        tabla_docentes(listar_docentes())
        did = pedir_int("ID de docente")
        if did is None:
            return
        tabla_cohortes(listar_cohortes(solo_activas=False))
        coh_id = pedir_int("ID de cohorte")
        if coh_id is None:
            return
        concepto = Prompt.ask("[white]  Concepto / descripción del material[/]").strip()
        if not concepto:
            err("El concepto es obligatorio.")
            return
        monto = pedir_float("Monto a pagar (₲)")
        obs = Prompt.ask("[white]  Observación (opcional)[/]", default="").strip()
        pid = registrar_pago_materiales_docente(did, coh_id, monto, concepto, obs)
        if pid:
            ok(f"Pago por materiales registrado con ID {pid}.")

    def _pendientes_docentes(self):
        pagos = listar_pagos_docente_pendientes()
        if not pagos:
            ok("No hay pagos pendientes de docentes.")
            return
        encabezado("PAGOS PENDIENTES — DOCENTES")
        tabla_pagos_docentes(pagos)
        total = sum(p["monto"] for p in pagos)
        console.print(f"\n  [bold yellow]  ⚠  Total pendiente: ₲ {int(total):,}[/]".replace(",", "."))

    def _marcar_pagado_docente(self):
        pagos = listar_pagos_docente_pendientes()
        if not pagos:
            ok("No hay pagos pendientes.")
            return
        tabla_pagos_docentes(pagos)
        pid = pedir_int("ID de pago a marcar como pagado")
        if pid is None:
            return
        pago = next((p for p in pagos if p["id"] == pid), None)
        if not pago:
            err("Pago no encontrado entre los pendientes.")
            return
        monto_str = f"₲ {int(pago['monto']):,}".replace(",", ".")
        if Confirm.ask(f"[yellow]  ¿Confirma marcar como pagado: {monto_str} a '{pago['docente']}'?[/]"):
            ok("Marcado como pagado.") if marcar_pago_docente_pagado(pid) else err("Error al actualizar.")

    def _anular_docente(self):
        tabla_docentes(listar_docentes())
        did = pedir_int("ID de docente")
        if did is None:
            return
        pagos = listar_pagos_docente(docente_id=did)
        tabla_pagos_docentes(pagos)
        if not pagos:
            return
        pid = pedir_int("ID de pago a anular")
        if pid is None:
            return
        pago = next((p for p in pagos if p["id"] == pid), None)
        if not pago:
            err("Pago no encontrado.")
            return
        if pago["estado"] == "anulado":
            warn("Este pago ya está anulado.")
            return
        monto_str = f"₲ {int(pago['monto']):,}".replace(",", ".")
        if Confirm.ask(f"[yellow]  ¿Confirma anular pago {monto_str} a '{pago['docente']}'?[/]"):
            ok("Pago anulado.") if anular_pago_docente(pid) else err("Error al anular.")

    def _resumen_cohorte(self):
        tabla_cohortes(listar_cohortes(solo_activas=False))
        coh_id = pedir_int("ID de cohorte")
        if coh_id is None:
            return
        cohorte = obtener_cohorte(coh_id)
        if not cohorte:
            err("Cohorte no encontrada.")
            return
        r = resumen_pagos_cohorte(coh_id)
        t = Table(box=box.DOUBLE_EDGE, border_style="cyan", show_header=False, padding=(0, 3))
        t.add_column("Concepto", style="white")
        t.add_column("Monto", style="bold", justify="right")
        t.add_row("Recaudado de estudiantes", f"[green]₲ {int(r['total_estudiantes']):,}[/]".replace(",", "."))
        t.add_row("Pagado a docentes",        f"[red]₲ {int(r['total_docentes']):,}[/]".replace(",", "."))
        bal_color = "green" if r["balance"] >= 0 else "red"
        t.add_row("Balance",                  f"[{bal_color}]₲ {int(r['balance']):,}[/{bal_color}]".replace(",", "."))
        console.print()
        console.print(Panel(t, title=f"[bold cyan]Resumen: {cohorte['nombre']} — {cohorte['curso']}[/]",
                            border_style="cyan", box=box.ROUNDED))
