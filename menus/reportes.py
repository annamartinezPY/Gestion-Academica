from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box
from ui.helpers import console, limpiar, encabezado, ok, err, warn, mostrar_menu, pausar, pedir_int, exportar_csv
from ui.tables import tabla_cohortes
from controllers.cohorte_controller import listar_cohortes, obtener_cohorte
from controllers.reporte_controller import (
    reporte_cursos, reporte_cohortes, reporte_participacion_cohorte,
    reporte_docentes, reporte_financiero_global, reporte_inscripciones_periodo,
)
from controllers.config_controller import obtener_config


class MenuReportes:

    def mostrar(self):
        while True:
            limpiar()
            encabezado("REPORTES ACADÉMICOS Y ADMINISTRATIVOS")
            op = mostrar_menu("Reportes", [
                "Reporte de cursos", "Reporte de cohortes",
                "Reporte de participación de una cohorte", "Reporte de docentes",
                "Reporte financiero global", "Reporte de inscripciones por período",
                "Exportar reporte a CSV", "Volver",
            ])
            if op == "1":
                self._cursos()
            elif op == "2":
                self._cohortes()
            elif op == "3":
                self._participacion()
            elif op == "4":
                self._docentes()
            elif op == "5":
                self._financiero()
            elif op == "6":
                self._inscripciones()
            elif op == "7":
                self._exportar()
            elif op == "8":
                break
            else:
                err("Opción inválida.")
            pausar()

    def _cursos(self):
        datos = reporte_cursos()
        if not datos:
            warn("No hay cursos.")
            return
        t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan", title="[bold]Cursos[/]")
        t.add_column("ID", style="dim", width=5)
        t.add_column("Curso", min_width=22)
        t.add_column("Modalidad", min_width=12)
        t.add_column("Horas", justify="right", width=7)
        t.add_column("Tarifa", justify="right", min_width=14)
        t.add_column("Cohortes", justify="right", width=9)
        t.add_column("Inscriptos", justify="right", width=10)
        t.add_column("Activo", justify="center", width=8)
        for d in datos:
            activo = "[green]Sí[/]" if d["activo"] else "[red]No[/]"
            tarifa = f"[cyan]₲ {int(d['tarifa_estudiante']):,}[/]".replace(",", ".")
            t.add_row(str(d["id"]), d["curso"], d["modalidad"],
                      str(d["horas_totales"]), tarifa,
                      str(d["total_cohortes"]), f"[cyan]{d['total_inscriptos']}[/]", activo)
        console.print(t)

    def _cohortes(self):
        datos = reporte_cohortes(solo_activas=False)
        if not datos:
            warn("No hay cohortes.")
            return
        t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan", title="[bold]Cohortes[/]")
        t.add_column("ID", style="dim", width=5)
        t.add_column("Cohorte", min_width=14)
        t.add_column("Curso", min_width=18)
        t.add_column("Modalidad", min_width=11)
        t.add_column("Período", min_width=22)
        t.add_column("Ocup.%", justify="right", width=8)
        t.add_column("Sesiones", justify="right", width=9)
        t.add_column("Ingresos", justify="right", min_width=14)
        t.add_column("Balance", justify="right", min_width=14)
        for d in datos:
            pct_color = "green" if d["ocupacion_pct"] >= 75 else ("yellow" if d["ocupacion_pct"] >= 40 else "red")
            bal_color = "green" if d["balance"] >= 0 else "red"
            t.add_row(
                str(d["id"]), d["cohorte"], d["curso"], d["modalidad"],
                f"{d['fecha_inicio']} → {d['fecha_fin']}",
                f"[{pct_color}]{d['ocupacion_pct']}%[/]", str(d["total_sesiones"]),
                f"[green]₲ {int(d['ingresos_estudiantes']):,}[/]".replace(",", "."),
                f"[{bal_color}]₲ {int(d['balance']):,}[/{bal_color}]".replace(",", "."),
            )
        console.print(t)

    def _participacion(self):
        tabla_cohortes(listar_cohortes(solo_activas=False))
        cid = pedir_int("ID de cohorte")
        if cid is None:
            return
        cohorte = obtener_cohorte(cid)
        if not cohorte:
            err("Cohorte no encontrada.")
            return
        datos = reporte_participacion_cohorte(cid)
        if not datos:
            warn("Sin estudiantes en esta cohorte.")
            return
        encabezado(f"Participación: {cohorte['nombre']} — {cohorte['curso']}")
        t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
        t.add_column("Estudiante", min_width=24)
        t.add_column("Estado", min_width=10)
        t.add_column("Sesiones", justify="right", width=9)
        t.add_column("Presentes", justify="right", width=10)
        t.add_column("Asist.%", justify="right", width=9)
        t.add_column("Total pagado", justify="right", min_width=14)
        t.add_column("Aprobado", justify="center", width=10)
        for e in datos:
            pct = e["pct_asistencia"]
            pct_color = "green" if pct >= 75 else ("yellow" if pct >= 50 else "red")
            aprobado = "[green]Sí[/]" if e["aprobado"] else "[red]No[/]"
            estado_color = "green" if e["estado_inscripcion"] == "activa" else "red"
            t.add_row(
                e["estudiante"],
                f"[{estado_color}]{e['estado_inscripcion']}[/]",
                str(e["total_sesiones"]), str(e["presentes"]),
                f"[{pct_color}]{pct}%[/]",
                f"[cyan]₲ {int(e['total_pagado']):,}[/]".replace(",", "."),
                aprobado,
            )
        console.print(t)

    def _docentes(self):
        datos = reporte_docentes()
        if not datos:
            warn("No hay docentes.")
            return
        t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan", title="[bold]Actividad de Docentes[/]")
        t.add_column("Docente", min_width=22)
        t.add_column("Especialidad", min_width=16)
        t.add_column("Tarifa/h", justify="right", min_width=14)
        t.add_column("Cohortes", justify="right", width=9)
        t.add_column("Hs dictadas", justify="right", width=12)
        t.add_column("Total cobrado", justify="right", min_width=14)
        for d in datos:
            t.add_row(
                d["docente"], d["especialidad"] or "",
                f"[cyan]₲ {int(d['tarifa_hora']):,}[/]".replace(",", "."),
                str(d["cohortes_asignadas"]),
                f"{d['horas_dictadas_sesiones']:.1f}h",
                f"[green]₲ {int(d['total_cobrado']):,}[/]".replace(",", "."),
            )
        console.print(t)

    def _financiero(self):
        r = reporte_financiero_global()
        moneda = obtener_config("moneda") or "PYG"
        bal_color = "green" if r["balance"] >= 0 else "red"
        resumen = Table(box=box.DOUBLE_EDGE, border_style="cyan", show_header=False, padding=(0, 3))
        resumen.add_column("Concepto", style="white")
        resumen.add_column("Monto", style="bold", justify="right")

        def gs(v):
            return f"₲ {int(v):,}".replace(",", ".")

        resumen.add_row("Ingresos (estudiantes)",   f"[green]{gs(r['total_ingresos'])} {moneda}[/]")
        resumen.add_row("Egresos (docentes)",        f"[red]{gs(r['total_egresos'])} {moneda}[/]")
        resumen.add_row("Balance",                   f"[{bal_color}]{gs(r['balance'])} {moneda}[/]")
        resumen.add_row("Pagos pendientes docentes", f"[yellow]{gs(r['pagos_pendientes_docentes'])} {moneda}[/]")
        console.print()
        console.print(Panel(resumen, title="[bold cyan]Resumen Financiero Global[/]", border_style="cyan", box=box.ROUNDED))
        if r["ingresos_por_modalidad"]:
            tm = Table(box=box.SIMPLE, header_style="bold cyan", title="[cyan]Ingresos por modalidad[/]")
            tm.add_column("Modalidad"); tm.add_column("Pagos", justify="right"); tm.add_column("Total", justify="right")
            for m in r["ingresos_por_modalidad"]:
                tm.add_row(m["modalidad"], str(m["cantidad_pagos"]), f"[green]{gs(m['total'])}[/]")
            console.print(); console.print(tm)
        if r["egresos_por_tipo"]:
            te = Table(box=box.SIMPLE, header_style="bold cyan", title="[cyan]Egresos por tipo[/]")
            te.add_column("Tipo"); te.add_column("Pagos", justify="right"); te.add_column("Total", justify="right")
            for e in r["egresos_por_tipo"]:
                te.add_row(e["tipo"].capitalize(), str(e["cantidad_pagos"]), f"[red]{gs(e['total'])}[/]")
            console.print(); console.print(te)

    def _inscripciones(self):
        anio_str = Prompt.ask("[white]  Año a consultar (Enter = todos)[/]", default="").strip()
        anio = anio_str if anio_str and anio_str.isdigit() else None
        datos = reporte_inscripciones_periodo(anio)
        if not datos:
            warn("Sin datos de inscripciones.")
            return
        t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan",
                  title=f"[bold]Inscripciones {'— ' + anio if anio else '(todos los años)'}[/]")
        t.add_column("Mes", min_width=8); t.add_column("Curso", min_width=22)
        t.add_column("Modalidad", min_width=11)
        t.add_column("Inscriptos", justify="right", min_width=10)
        t.add_column("Canceladas", justify="right", min_width=10)
        for d in datos:
            t.add_row(d["mes"], d["curso"], d["modalidad"],
                      f"[cyan]{d['inscriptos']}[/]", f"[red]{d['canceladas']}[/]")
        console.print(t)

    def _exportar(self):
        op = mostrar_menu("¿Qué reporte exportar?", [
            "Cursos", "Cohortes", "Docentes", "Inscripciones por período", "Volver",
        ])
        if op == "1":
            exportar_csv(reporte_cursos(), "reporte_cursos.csv")
        elif op == "2":
            exportar_csv(reporte_cohortes(solo_activas=False), "reporte_cohortes.csv")
        elif op == "3":
            exportar_csv(reporte_docentes(), "reporte_docentes.csv")
        elif op == "4":
            anio_str = Prompt.ask("[white]  Año (Enter = todos)[/]", default="").strip()
            anio = anio_str if anio_str and anio_str.isdigit() else None
            exportar_csv(reporte_inscripciones_periodo(anio), "reporte_inscripciones.csv")
