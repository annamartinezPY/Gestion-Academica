"""Funciones de renderizado de tablas Rich para cada entidad del sistema."""
from rich.table import Table
from rich import box
from ui.helpers import console, warn


def tabla_usuarios(usuarios):
    if not usuarios:
        warn("No hay usuarios registrados.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan", show_lines=False)
    t.add_column("ID", style="dim", width=5)
    t.add_column("Nombre", min_width=22)
    t.add_column("Email", min_width=26)
    t.add_column("Rol", min_width=12)
    t.add_column("Activo", justify="center", width=8)
    for u in usuarios:
        activo = "[green]Sí[/]" if u["activo"] else "[red]No[/]"
        t.add_row(str(u["id"]), f"{u['nombre']} {u['apellido']}", u["email"], u["rol"], activo)
    console.print(t)


def tabla_estudiantes(estudiantes):
    if not estudiantes:
        warn("No hay estudiantes registrados.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("ID", style="dim", width=5)
    t.add_column("Nombre", min_width=22)
    t.add_column("Documento", min_width=12)
    t.add_column("Teléfono", min_width=12)
    t.add_column("Email", min_width=26)
    for e in estudiantes:
        t.add_row(
            str(e["id"]), f"{e['nombre']} {e['apellido']}",
            e["documento"] or "", e["telefono"] or "", e["email"],
        )
    console.print(t)


def tabla_docentes(docentes):
    if not docentes:
        warn("No hay docentes registrados.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("ID", style="dim", width=5)
    t.add_column("Nombre", min_width=22)
    t.add_column("Especialidad", min_width=18)
    t.add_column("Tarifa/h", justify="right", min_width=10)
    t.add_column("Email", min_width=26)
    for d in docentes:
        t.add_row(
            str(d["id"]), f"{d['nombre']} {d['apellido']}",
            d["especialidad"] or "", f"[cyan]₲ {int(d['tarifa_hora']):,}[/]".replace(",", "."),
            d["email"],
        )
    console.print(t)


def tabla_cursos(cursos):
    if not cursos:
        warn("No hay cursos registrados.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("ID", style="dim", width=5)
    t.add_column("Nombre", min_width=22)
    t.add_column("Modalidad", min_width=12)
    t.add_column("Horas", justify="right", width=7)
    t.add_column("Tarifa", justify="right", min_width=12)
    t.add_column("Activo", justify="center", width=8)
    for c in cursos:
        activo = "[green]Sí[/]" if c["activo"] else "[red]No[/]"
        t.add_row(
            str(c["id"]), c["nombre"], c["modalidad"],
            str(c["horas_totales"]),
            f"[cyan]₲ {int(c['tarifa_estudiante']):,}[/]".replace(",", "."),
            activo,
        )
    console.print(t)


def tabla_cohortes(cohortes):
    if not cohortes:
        warn("No hay cohortes registradas.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("ID", style="dim", width=5)
    t.add_column("Nombre", min_width=15)
    t.add_column("Curso", min_width=20)
    t.add_column("Inicio", min_width=12)
    t.add_column("Fin", min_width=12)
    t.add_column("Cupo", justify="right", width=6)
    t.add_column("Inscr.", justify="right", width=7)
    for co in cohortes:
        lleno = co["inscriptos"] >= co["cupo_maximo"]
        inscr = f"[red]{co['inscriptos']}[/]" if lleno else f"[green]{co['inscriptos']}[/]"
        t.add_row(
            str(co["id"]), co["nombre"], co["curso"],
            co["fecha_inicio"], co["fecha_fin"], str(co["cupo_maximo"]), inscr,
        )
    console.print(t)


def tabla_sesiones(sesiones):
    if not sesiones:
        warn("No hay sesiones registradas para esta cohorte.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("ID", style="dim", width=5)
    t.add_column("Fecha", min_width=12)
    t.add_column("Inicio", width=8)
    t.add_column("Fin", width=8)
    t.add_column("Docente", min_width=22)
    t.add_column("Tema")
    for s in sesiones:
        t.add_row(str(s["id"]), s["fecha"], s["hora_inicio"], s["hora_fin"], s["docente"], s["tema"] or "")
    console.print(t)


def tabla_inscripciones(inscripciones):
    if not inscripciones:
        warn("No hay inscripciones registradas.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("ID", style="dim", width=5)
    t.add_column("Estudiante", min_width=22)
    t.add_column("Email", min_width=22)
    t.add_column("Cohorte", min_width=15)
    t.add_column("Curso", min_width=18)
    t.add_column("Estado", min_width=10)
    t.add_column("Fecha", min_width=12)
    for i in inscripciones:
        color = "green" if i["estado"] == "activa" else "red"
        t.add_row(
            str(i["id"]), i["estudiante"], i["email"],
            i["cohorte"], i["curso"],
            f"[{color}]{i['estado']}[/]",
            i["fecha_inscripcion"][:10],
        )
    console.print(t)


def tabla_pagos_estudiantes(pagos):
    if not pagos:
        warn("No hay pagos registrados.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("ID", style="dim", width=5)
    t.add_column("Estudiante", min_width=20)
    t.add_column("Curso / Cohorte", min_width=22)
    t.add_column("Monto", justify="right", min_width=14)
    t.add_column("Método", min_width=12)
    t.add_column("Estado", min_width=10)
    t.add_column("Fecha", min_width=12)
    for p in pagos:
        monto = f"[green]₲ {int(p['monto']):,}[/]".replace(",", ".")
        t.add_row(
            str(p["id"]), p["estudiante"], f"{p['curso']} / {p['cohorte']}",
            monto, p["metodo_pago"], p["estado"], p["fecha_pago"][:10],
        )
    console.print(t)


def tabla_pagos_docentes(pagos):
    if not pagos:
        warn("No hay pagos registrados.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("ID", style="dim", width=5)
    t.add_column("Docente", min_width=20)
    t.add_column("Curso / Cohorte", min_width=22)
    t.add_column("Tipo", min_width=11)
    t.add_column("Concepto / Horas", min_width=16)
    t.add_column("Monto", justify="right", min_width=14)
    t.add_column("Estado", min_width=12)
    t.add_column("Fecha", min_width=12)
    for p in pagos:
        color = "green" if p["estado"] == "pagado" else "yellow"
        tipo = p.get("tipo_pago", "horas")
        tipo_str = "[magenta]Materiales[/]" if tipo == "materiales" else "[cyan]Horas[/]"
        concepto = p.get("concepto") or "" if tipo == "materiales" else str(p["horas_dictadas"]) + "h"
        monto = f"[cyan]₲ {int(p['monto']):,}[/]".replace(",", ".")
        t.add_row(
            str(p["id"]), p["docente"], f"{p['curso']} / {p['cohorte']}",
            tipo_str, concepto, monto,
            f"[{color}]{p['estado']}[/]", p["fecha_pago"][:10],
        )
    console.print(t)


def tabla_asistencia_sesion(registros):
    if not registros:
        warn("No hay estudiantes en esta sesión.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("Est.ID", style="dim", width=7)
    t.add_column("Estudiante", min_width=24)
    t.add_column("Email", min_width=22)
    t.add_column("Asistencia", justify="center", min_width=12)
    t.add_column("Observación")
    for r in registros:
        if r["presente"] == 1:
            estado = "[green]Presente[/]"
        elif r["presente"] == 0:
            estado = "[red]Ausente[/]"
        else:
            estado = "[dim]Sin registrar[/]"
        t.add_row(str(r["estudiante_id"]), r["estudiante"], r["email"], estado, r["observacion"] or "")
    console.print(t)


def tabla_resumen_asistencia(estudiantes):
    if not estudiantes:
        warn("No hay estudiantes inscriptos.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("Estudiante", min_width=24)
    t.add_column("Sesiones", justify="right", width=9)
    t.add_column("Presentes", justify="right", width=10)
    t.add_column("Ausentes", justify="right", width=9)
    t.add_column("Asistencia %", justify="right", min_width=13)
    for e in estudiantes:
        pct = e["porcentaje"]
        color = "green" if pct >= 75 else ("yellow" if pct >= 50 else "red")
        t.add_row(
            e["estudiante"], str(e["total_sesiones"]),
            f"[green]{e['presentes']}[/]", f"[red]{e['ausentes']}[/]",
            f"[{color}]{pct}%[/]",
        )
    console.print(t)
