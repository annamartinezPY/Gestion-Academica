"""
Plataforma de Gestión Académica — Punto de entrada principal.
Interfaz moderna con Rich TUI.
"""
import csv
import os
import re

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.align import Align
from rich import box

from database import inicializar_db, get_connection
from controllers.usuario_controller import (
    login, registrar_usuario, listar_usuarios,
    actualizar_usuario, desactivar_usuario,
)
from controllers.estudiante_controller import (
    registrar_estudiante, listar_estudiantes,
    obtener_estudiante, actualizar_estudiante,
    buscar_estudiante_por_documento,
)
from controllers.docente_controller import (
    registrar_docente, listar_docentes,
    obtener_docente, actualizar_docente,
    desactivar_docente, listar_cohortes_docente,
    buscar_docente_por_email,
)
from controllers.curso_controller import (
    registrar_curso, listar_cursos, obtener_curso,
    actualizar_curso, desactivar_curso, listar_modalidades,
)
from controllers.cohorte_controller import (
    registrar_cohorte, listar_cohortes, obtener_cohorte,
    actualizar_cohorte, registrar_sesion, listar_sesiones,
    cupo_disponible, desactivar_cohorte,
    obtener_sesion, actualizar_sesion, eliminar_sesion,
    contar_inscriptos,
)
from controllers.inscripcion_controller import (
    inscribir_estudiante, listar_inscripciones,
    obtener_inscripcion, cancelar_inscripcion,
    reactivar_inscripcion, listar_inscripciones_pendientes_pago,
)
from controllers.pago_controller import (
    registrar_pago_estudiante, listar_pagos_estudiante,
    anular_pago_estudiante, listar_pagos_cohorte,
    registrar_pago_docente, registrar_pago_materiales_docente,
    listar_pagos_docente, listar_pagos_docente_pendientes,
    marcar_pago_docente_pagado, anular_pago_docente,
    resumen_pagos_cohorte,
)
from controllers.asistencia_controller import (
    registrar_asistencia, listar_asistencia_sesion,
    listar_asistencia_estudiante, resumen_asistencia_cohorte,
)
from controllers.reporte_controller import (
    reporte_cursos, reporte_cohortes, reporte_participacion_cohorte,
    reporte_docentes, reporte_financiero_global, reporte_inscripciones_periodo,
)
from controllers.config_controller import (
    listar_config, obtener_config, actualizar_config,
    listar_modalidades as cfg_listar_modalidades,
    agregar_modalidad, actualizar_modalidad,
    listar_roles, agregar_rol,
    obtener_condiciones_curso, actualizar_condiciones_curso,
)

console = Console()


# ══════════════════════════════════════════════════════════════════
#  Helpers de UI
# ══════════════════════════════════════════════════════════════════

def limpiar():
    console.clear()


def encabezado(titulo, subtitulo=""):
    console.print()
    texto = Text(justify="center")
    texto.append(titulo, style="bold cyan")
    if subtitulo:
        texto.append(f"\n{subtitulo}", style="dim white")
    console.print(Panel(
        Align.center(texto),
        box=box.DOUBLE_EDGE,
        border_style="cyan",
        padding=(0, 4),
    ))


def ok(msg):
    console.print(f"\n[bold green]  ✔  {msg}[/]")


def err(msg):
    console.print(f"\n[bold red]  ✖  {msg}[/]")


def warn(msg):
    console.print(f"\n[bold yellow]  ⚠  {msg}[/]")


def pausar():
    console.print()
    Prompt.ask("[dim]  Presione Enter para continuar[/]", default="")


def mostrar_menu(titulo, opciones):
    """Dibuja un panel de menú y retorna la opción ingresada."""
    texto = Text()
    for i, op in enumerate(opciones, 1):
        texto.append(f"  [{i}]  ", style="bold cyan")
        texto.append(f"{op}\n", style="white")
    console.print()
    console.print(Panel(
        texto,
        title=f"[bold cyan]{titulo}[/]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(0, 1),
    ))
    return Prompt.ask("[cyan]  Opción[/]").strip()


def pedir_int(prompt):
    val = Prompt.ask(f"[white]  {prompt}[/]").strip()
    try:
        return int(val)
    except ValueError:
        err("Valor numérico inválido.")
        return None


def pedir_float(prompt, default=0.0):
    val = Prompt.ask(f"[white]  {prompt}[/]", default=str(default)).strip()
    try:
        return float(val)
    except ValueError:
        err("Valor decimal inválido.")
        return default


def pedir_fecha(prompt):
    """Solicita una fecha en formato YYYY-MM-DD con validación."""
    while True:
        val = Prompt.ask(f"[white]  {prompt} [dim](YYYY-MM-DD)[/][/]").strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", val):
            return val
        err("Formato inválido. Use YYYY-MM-DD  (ej: 2025-06-15)")


def exportar_csv(datos, nombre_archivo):
    """Exporta una lista de dicts a un archivo CSV."""
    if not datos:
        warn("No hay datos para exportar.")
        return
    try:
        with open(nombre_archivo, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=datos[0].keys())
            writer.writeheader()
            writer.writerows(datos)
        ok(f"Exportado a [bold]{nombre_archivo}[/]")
    except Exception as e:
        err(f"Error al exportar: {e}")


# ══════════════════════════════════════════════════════════════════
#  Tablas de datos
# ══════════════════════════════════════════════════════════════════

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
            str(e["id"]),
            f"{e['nombre']} {e['apellido']}",
            e["documento"] or "",
            e["telefono"] or "",
            e["email"],
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
            str(d["id"]),
            f"{d['nombre']} {d['apellido']}",
            d["especialidad"] or "",
            f"[cyan]${d['tarifa_hora']:.2f}[/]",
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
    t.add_column("Tarifa", justify="right", min_width=10)
    t.add_column("Activo", justify="center", width=8)
    for c in cursos:
        activo = "[green]Sí[/]" if c["activo"] else "[red]No[/]"
        t.add_row(
            str(c["id"]), c["nombre"], c["modalidad"],
            str(c["horas_totales"]), f"[cyan]${c['tarifa_estudiante']:.2f}[/]", activo,
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
            co["fecha_inicio"], co["fecha_fin"],
            str(co["cupo_maximo"]), inscr,
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
    t.add_column("Monto", justify="right", min_width=10)
    t.add_column("Método", min_width=12)
    t.add_column("Estado", min_width=10)
    t.add_column("Fecha", min_width=12)
    for p in pagos:
        t.add_row(
            str(p["id"]), p["estudiante"], f"{p['curso']} / {p['cohorte']}",
            f"[green]${p['monto']:.2f}[/]", p["metodo_pago"],
            p["estado"], p["fecha_pago"][:10],
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
    t.add_column("Monto", justify="right", min_width=10)
    t.add_column("Estado", min_width=12)
    t.add_column("Fecha", min_width=12)
    for p in pagos:
        color = "green" if p["estado"] == "pagado" else "yellow"
        tipo = p.get("tipo_pago", "horas")
        if tipo == "materiales":
            tipo_str = "[magenta]Materiales[/]"
            concepto_horas = p.get("concepto") or ""
        else:
            tipo_str = "[cyan]Horas[/]"
            concepto_horas = str(p["horas_dictadas"]) + "h"
        t.add_row(
            str(p["id"]), p["docente"], f"{p['curso']} / {p['cohorte']}",
            tipo_str, concepto_horas,
            f"[cyan]${p['monto']:.2f}[/]",
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
        t.add_row(
            str(r["estudiante_id"]), r["estudiante"], r["email"],
            estado, r["observacion"] or "",
        )
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
            e["estudiante"],
            str(e["total_sesiones"]),
            f"[green]{e['presentes']}[/]",
            f"[red]{e['ausentes']}[/]",
            f"[{color}]{pct}%[/]",
        )
    console.print(t)


# ══════════════════════════════════════════════════════════════════
#  Pantalla de login
# ══════════════════════════════════════════════════════════════════

def pantalla_login():
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
    err("Credenciales incorrectas o usuario inactivo.")
    pausar()
    return None


# ══════════════════════════════════════════════════════════════════
#  Admin — Usuarios
# ══════════════════════════════════════════════════════════════════

def menu_usuarios():
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
            _registrar_usuario()
        elif op == "3":
            _actualizar_usuario()
        elif op == "4":
            _desactivar_usuario()
        elif op == "5":
            break
        else:
            err("Opción inválida.")
        pausar()


def _registrar_usuario():
    console.print(Panel("[bold cyan]REGISTRAR USUARIO[/]", box=box.ROUNDED, border_style="cyan"))
    nombre = Prompt.ask("[white]  Nombre[/]").strip()
    apellido = Prompt.ask("[white]  Apellido[/]").strip()
    email = Prompt.ask("[white]  Email[/]").strip()
    password = Prompt.ask("[white]  Contraseña[/]", password=True).strip()
    console.print("  Roles: [cyan]admin[/], [cyan]docente[/], [cyan]estudiante[/]")
    rol = Prompt.ask("[white]  Rol[/]").strip().lower()
    uid = registrar_usuario(nombre, apellido, email, password, rol)
    if uid:
        ok(f"Usuario registrado con ID {uid}.")


def _actualizar_usuario():
    tabla_usuarios(listar_usuarios())
    uid = pedir_int("ID a actualizar")
    if uid is None:
        return
    nombre = Prompt.ask("[white]  Nuevo nombre (Enter = sin cambio)[/]", default="").strip() or None
    apellido = Prompt.ask("[white]  Nuevo apellido (Enter = sin cambio)[/]", default="").strip() or None
    email = Prompt.ask("[white]  Nuevo email (Enter = sin cambio)[/]", default="").strip() or None
    if actualizar_usuario(uid, nombre, apellido, email):
        ok("Usuario actualizado.")


def _desactivar_usuario():
    tabla_usuarios(listar_usuarios())
    uid = pedir_int("ID a desactivar")
    if uid is None:
        return
    if Confirm.ask(f"[yellow]  ¿Confirma desactivar usuario {uid}?[/]"):
        ok("Desactivado.") if desactivar_usuario(uid) else err("No encontrado.")


# ══════════════════════════════════════════════════════════════════
#  Admin — Estudiantes
# ══════════════════════════════════════════════════════════════════

def menu_estudiantes():
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
            _registrar_estudiante()
        elif op == "3":
            _buscar_estudiante()
        elif op == "4":
            _actualizar_estudiante()
        elif op == "5":
            break
        else:
            err("Opción inválida.")
        pausar()


def _registrar_estudiante():
    console.print(Panel("[bold cyan]REGISTRAR ESTUDIANTE[/]", box=box.ROUNDED, border_style="cyan"))
    nombre = Prompt.ask("[white]  Nombre[/]").strip()
    apellido = Prompt.ask("[white]  Apellido[/]").strip()
    email = Prompt.ask("[white]  Email[/]").strip()
    password = Prompt.ask("[white]  Contraseña[/]", password=True).strip()
    documento = Prompt.ask("[white]  Documento (CI/Pasaporte)[/]").strip()
    telefono = Prompt.ask("[white]  Teléfono (opcional)[/]", default="").strip()
    eid = registrar_estudiante(nombre, apellido, email, password, documento, telefono)
    if eid:
        ok(f"Estudiante registrado con ID {eid}.")


def _buscar_estudiante():
    doc = Prompt.ask("[white]  Número de documento[/]").strip()
    e = buscar_estudiante_por_documento(doc)
    if e:
        console.print(Panel(
            f"[white]ID:[/] [cyan]{e['id']}[/]   "
            f"[white]Nombre:[/] [cyan]{e['nombre']} {e['apellido']}[/]   "
            f"[white]Email:[/] [cyan]{e['email']}[/]",
            title="[green]Estudiante encontrado[/]",
            border_style="green",
            box=box.ROUNDED,
        ))
    else:
        err("No se encontró ningún estudiante con ese documento.")


def _actualizar_estudiante():
    tabla_estudiantes(listar_estudiantes())
    eid = pedir_int("ID a actualizar")
    if eid is None:
        return
    documento = Prompt.ask("[white]  Nuevo documento (Enter = sin cambio)[/]", default="").strip() or None
    telefono = Prompt.ask("[white]  Nuevo teléfono (Enter = sin cambio)[/]", default="").strip() or None
    if actualizar_estudiante(eid, documento, telefono):
        ok("Estudiante actualizado.")


# ══════════════════════════════════════════════════════════════════
#  Admin — Docentes
# ══════════════════════════════════════════════════════════════════

def menu_docentes():
    while True:
        limpiar()
        encabezado("GESTIÓN DE DOCENTES")
        op = mostrar_menu("Docentes", [
            "Listar docentes",
            "Registrar docente",
            "Actualizar docente",
            "Ver cohortes de un docente",
            "Buscar docente por email",
            "Desactivar docente",
            "Volver",
        ])
        if op == "1":
            tabla_docentes(listar_docentes())
        elif op == "2":
            _registrar_docente()
        elif op == "3":
            _actualizar_docente()
        elif op == "4":
            _cohortes_docente()
        elif op == "5":
            _buscar_docente()
        elif op == "6":
            _desactivar_docente()
        elif op == "7":
            break
        else:
            err("Opción inválida.")
        pausar()


def _registrar_docente():
    console.print(Panel("[bold cyan]REGISTRAR DOCENTE[/]", box=box.ROUNDED, border_style="cyan"))
    nombre = Prompt.ask("[white]  Nombre[/]").strip()
    apellido = Prompt.ask("[white]  Apellido[/]").strip()
    email = Prompt.ask("[white]  Email[/]").strip()
    password = Prompt.ask("[white]  Contraseña[/]", password=True).strip()
    especialidad = Prompt.ask("[white]  Especialidad (opcional)[/]", default="").strip()
    tarifa = pedir_float("Tarifa por hora", 0.0)
    did = registrar_docente(nombre, apellido, email, password, especialidad, tarifa)
    if did:
        ok(f"Docente registrado con ID {did}.")


def _actualizar_docente():
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
        f"[white]  Especialidad (Enter = [dim]{d['especialidad'] or 'vacía'}[/])[/]",
        default=""
    ).strip() or None
    tarifa_str = Prompt.ask(
        f"[white]  Tarifa/hora (Enter = [dim]{d['tarifa_hora']:.2f}[/])[/]",
        default=""
    ).strip()
    tarifa = float(tarifa_str) if tarifa_str else None
    if actualizar_docente(did, especialidad, tarifa):
        ok("Docente actualizado.")


def _cohortes_docente():
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


def _buscar_docente():
    email = Prompt.ask("[white]  Email del docente[/]").strip()
    d = buscar_docente_por_email(email)
    if d:
        console.print(Panel(
            f"[white]ID:[/] [cyan]{d['id']}[/]   "
            f"[white]Nombre:[/] [cyan]{d['nombre']} {d['apellido']}[/]\n"
            f"[white]Especialidad:[/] [cyan]{d['especialidad'] or 'N/A'}[/]   "
            f"[white]Tarifa:[/] [cyan]${d['tarifa_hora']:.2f}/h[/]   "
            f"[white]Activo:[/] {'[green]Sí[/]' if d['activo'] else '[red]No[/]'}",
            title="[green]Docente encontrado[/]",
            border_style="green",
            box=box.ROUNDED,
        ))
    else:
        err("No se encontró ningún docente con ese email.")


def _desactivar_docente():
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


# ══════════════════════════════════════════════════════════════════
#  Admin — Cursos
# ══════════════════════════════════════════════════════════════════

def menu_cursos():
    while True:
        limpiar()
        encabezado("GESTIÓN DE CURSOS")
        op = mostrar_menu("Cursos", [
            "Listar cursos", "Registrar curso",
            "Actualizar curso", "Desactivar curso", "Volver",
        ])
        if op == "1":
            tabla_cursos(listar_cursos(solo_activos=False))
        elif op == "2":
            _registrar_curso()
        elif op == "3":
            _actualizar_curso()
        elif op == "4":
            _desactivar_curso()
        elif op == "5":
            break
        else:
            err("Opción inválida.")
        pausar()


def _registrar_curso():
    console.print(Panel("[bold cyan]REGISTRAR CURSO[/]", box=box.ROUNDED, border_style="cyan"))
    modalidades = listar_modalidades()
    t = Table(box=box.SIMPLE, header_style="bold cyan")
    t.add_column("ID"); t.add_column("Modalidad"); t.add_column("Descripción")
    for m in modalidades:
        t.add_row(str(m["id"]), m["nombre"], m["descripcion"] or "")
    console.print(t)
    nombre = Prompt.ask("[white]  Nombre del curso[/]").strip()
    descripcion = Prompt.ask("[white]  Descripción[/]", default="").strip()
    modalidad_id = pedir_int("ID de modalidad")
    if modalidad_id is None:
        return
    horas_str = Prompt.ask("[white]  Horas totales[/]", default="0")
    tarifa_str = Prompt.ask("[white]  Tarifa para estudiantes[/]", default="0")
    try:
        horas = int(horas_str)
        tarifa = float(tarifa_str)
    except ValueError:
        err("Valores numéricos inválidos.")
        return
    cid = registrar_curso(nombre, descripcion, modalidad_id, horas, tarifa)
    if cid:
        ok(f"Curso registrado con ID {cid}.")


def _actualizar_curso():
    tabla_cursos(listar_cursos(solo_activos=False))
    cid = pedir_int("ID a actualizar")
    if cid is None:
        return
    nombre = Prompt.ask("[white]  Nuevo nombre (Enter = sin cambio)[/]", default="").strip() or None
    descripcion = Prompt.ask("[white]  Nueva descripción (Enter = sin cambio)[/]", default="").strip() or None
    horas_str = Prompt.ask("[white]  Nuevas horas totales (Enter = sin cambio)[/]", default="").strip()
    tarifa_str = Prompt.ask("[white]  Nueva tarifa (Enter = sin cambio)[/]", default="").strip()
    horas = int(horas_str) if horas_str else None
    tarifa = float(tarifa_str) if tarifa_str else None
    if actualizar_curso(cid, nombre, descripcion, horas_totales=horas, tarifa_estudiante=tarifa):
        ok("Curso actualizado.")


def _desactivar_curso():
    tabla_cursos(listar_cursos(solo_activos=False))
    cid = pedir_int("ID a desactivar")
    if cid is None:
        return
    if Confirm.ask(f"[yellow]  ¿Confirma desactivar curso {cid}?[/]"):
        ok("Desactivado.") if desactivar_curso(cid) else err("No encontrado.")


# ══════════════════════════════════════════════════════════════════
#  Admin — Cohortes
# ══════════════════════════════════════════════════════════════════

def menu_cohortes():
    while True:
        limpiar()
        encabezado("GESTIÓN DE COHORTES")
        op = mostrar_menu("Cohortes", [
            "Listar todas las cohortes",
            "Registrar cohorte",
            "Actualizar cohorte",
            "Desactivar cohorte",
            "Cohortes de un curso",
            "Registrar sesión de clase",
            "Ver sesiones de una cohorte",
            "Editar sesión",
            "Eliminar sesión",
            "Volver",
        ])
        if op == "1":
            tabla_cohortes(listar_cohortes(solo_activas=False))
        elif op == "2":
            _registrar_cohorte()
        elif op == "3":
            _actualizar_cohorte()
        elif op == "4":
            _desactivar_cohorte()
        elif op == "5":
            _cohortes_de_curso()
        elif op == "6":
            _registrar_sesion()
        elif op == "7":
            _ver_sesiones()
        elif op == "8":
            _editar_sesion()
        elif op == "9":
            _eliminar_sesion()
        elif op == "10":
            break
        else:
            err("Opción inválida.")
        pausar()


def _registrar_cohorte():
    console.print(Panel("[bold cyan]REGISTRAR COHORTE[/]", box=box.ROUNDED, border_style="cyan"))
    tabla_cursos(listar_cursos(solo_activos=True))
    curso_id = pedir_int("ID del curso")
    if curso_id is None:
        return
    curso = obtener_curso(curso_id)
    if not curso:
        err("Curso no encontrado.")
        return
    nombre = Prompt.ask("[white]  Nombre de la cohorte (ej: 2025-A)[/]").strip()
    fecha_inicio = pedir_fecha("Fecha inicio")
    fecha_fin = pedir_fecha("Fecha fin")
    cupo_str = Prompt.ask("[white]  Cupo máximo[/]", default="30")
    try:
        cupo = int(cupo_str)
    except ValueError:
        cupo = 30
    coid = registrar_cohorte(nombre, curso_id, fecha_inicio, fecha_fin, cupo)
    if coid:
        ok(f"Cohorte '{nombre}' registrada con ID {coid} para '{curso['nombre']}'.")


def _actualizar_cohorte():
    tabla_cohortes(listar_cohortes(solo_activas=False))
    coid = pedir_int("ID de cohorte a actualizar")
    if coid is None:
        return
    cohorte = obtener_cohorte(coid)
    if not cohorte:
        err("Cohorte no encontrada.")
        return
    nombre = Prompt.ask(
        f"[white]  Nombre (Enter = [dim]{cohorte['nombre']}[/])[/]", default=""
    ).strip() or None
    fecha_inicio_str = Prompt.ask(
        f"[white]  Fecha inicio (Enter = [dim]{cohorte['fecha_inicio']}[/])[/]", default=""
    ).strip()
    fecha_fin_str = Prompt.ask(
        f"[white]  Fecha fin (Enter = [dim]{cohorte['fecha_fin']}[/])[/]", default=""
    ).strip()
    cupo_str = Prompt.ask(
        f"[white]  Cupo máximo (Enter = [dim]{cohorte['cupo_maximo']}[/])[/]", default=""
    ).strip()
    # Validar fechas si se ingresaron
    if fecha_inicio_str and not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha_inicio_str):
        err("Formato de fecha inválido. Use YYYY-MM-DD.")
        return
    if fecha_fin_str and not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha_fin_str):
        err("Formato de fecha inválido. Use YYYY-MM-DD.")
        return
    cupo = int(cupo_str) if cupo_str else None
    from controllers.cohorte_controller import actualizar_cohorte
    if actualizar_cohorte(coid, nombre, fecha_inicio_str or None, fecha_fin_str or None, cupo):
        ok("Cohorte actualizada.")
    else:
        err("No se pudo actualizar.")


def _cohortes_de_curso():
    tabla_cursos(listar_cursos(solo_activos=False))
    cid = pedir_int("ID del curso")
    if cid is None:
        return
    tabla_cohortes(listar_cohortes(curso_id=cid, solo_activas=False))


def _registrar_sesion():
    console.print(Panel("[bold cyan]REGISTRAR SESIÓN DE CLASE[/]", box=box.ROUNDED, border_style="cyan"))
    tabla_cohortes(listar_cohortes(solo_activas=False))
    cohorte_id = pedir_int("ID de cohorte")
    if cohorte_id is None:
        return
    tabla_docentes(listar_docentes())
    docente_id = pedir_int("ID de docente")
    if docente_id is None:
        return
    fecha = pedir_fecha("Fecha de la sesión")
    hora_inicio = Prompt.ask("[white]  Hora inicio (HH:MM)[/]").strip()
    hora_fin = Prompt.ask("[white]  Hora fin (HH:MM)[/]").strip()
    tema = Prompt.ask("[white]  Tema (opcional)[/]", default="").strip()
    sid = registrar_sesion(cohorte_id, docente_id, fecha, hora_inicio, hora_fin, tema)
    if sid:
        ok(f"Sesión registrada con ID {sid}.")


def _ver_sesiones():
    tabla_cohortes(listar_cohortes(solo_activas=False))
    cohorte_id = pedir_int("ID de cohorte")
    if cohorte_id is None:
        return
    sesiones = listar_sesiones(cohorte_id)
    tabla_sesiones(sesiones)
    if sesiones:
        total_h = sum(
            (int(s["hora_fin"][:2]) + int(s["hora_fin"][3:5]) / 60)
            - (int(s["hora_inicio"][:2]) + int(s["hora_inicio"][3:5]) / 60)
            for s in sesiones
        )
        console.print(f"  [dim]Total sesiones: {len(sesiones)}  |  Horas acumuladas: {total_h:.1f}h[/]")


def _desactivar_cohorte():
    tabla_cohortes(listar_cohortes(solo_activas=False))
    coid = pedir_int("ID de cohorte a desactivar")
    if coid is None:
        return
    cohorte = obtener_cohorte(coid)
    if not cohorte:
        err("Cohorte no encontrada.")
        return
    inscriptos = contar_inscriptos(coid)
    if inscriptos > 0:
        warn(f"Esta cohorte tiene {inscriptos} estudiante(s) inscripto(s).")
    if Confirm.ask(f"[yellow]  ¿Confirma desactivar '{cohorte['nombre']}'?[/]"):
        ok("Cohorte desactivada.") if desactivar_cohorte(coid) else err("No se pudo desactivar.")


def _editar_sesion():
    console.print(Panel("[bold cyan]EDITAR SESIÓN[/]", box=box.ROUNDED, border_style="cyan"))
    tabla_cohortes(listar_cohortes(solo_activas=False))
    cohorte_id = pedir_int("ID de cohorte")
    if cohorte_id is None:
        return
    tabla_sesiones(listar_sesiones(cohorte_id))
    sid = pedir_int("ID de sesión a editar")
    if sid is None:
        return
    sesion = obtener_sesion(sid)
    if not sesion:
        err("Sesión no encontrada.")
        return
    console.print(f"  [dim]Editando sesión del {sesion['fecha']} — {sesion['docente']}[/]")

    # Docente
    tabla_docentes(listar_docentes())
    did_str = Prompt.ask(
        f"[white]  Nuevo docente ID (Enter = [dim]{sesion['docente_id']}[/])[/]",
        default=""
    ).strip()
    nuevo_did = int(did_str) if did_str else None

    # Fecha y horarios
    fecha_str = Prompt.ask(
        f"[white]  Nueva fecha (Enter = [dim]{sesion['fecha']}[/])[/]",
        default=""
    ).strip()
    if fecha_str and not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha_str):
        err("Formato de fecha inválido.")
        return
    hi_str = Prompt.ask(
        f"[white]  Hora inicio (Enter = [dim]{sesion['hora_inicio']}[/])[/]",
        default=""
    ).strip()
    hf_str = Prompt.ask(
        f"[white]  Hora fin (Enter = [dim]{sesion['hora_fin']}[/])[/]",
        default=""
    ).strip()
    tema_str = Prompt.ask(
        f"[white]  Tema (Enter = [dim]{sesion['tema'] or 'vacío'}[/])[/]",
        default=""
    ).strip()

    if actualizar_sesion(
        sid,
        docente_id=nuevo_did,
        fecha=fecha_str or None,
        hora_inicio=hi_str or None,
        hora_fin=hf_str or None,
        tema=tema_str or None,
    ):
        ok("Sesión actualizada.")
    else:
        err("No se pudo actualizar.")


def _eliminar_sesion():
    tabla_cohortes(listar_cohortes(solo_activas=False))
    cohorte_id = pedir_int("ID de cohorte")
    if cohorte_id is None:
        return
    tabla_sesiones(listar_sesiones(cohorte_id))
    sid = pedir_int("ID de sesión a eliminar")
    if sid is None:
        return
    sesion = obtener_sesion(sid)
    if not sesion:
        err("Sesión no encontrada.")
        return
    warn("Se eliminarán también los registros de asistencia de esta sesión.")
    if Confirm.ask(f"[yellow]  ¿Confirma eliminar sesión del {sesion['fecha']}?[/]"):
        ok("Sesión eliminada.") if eliminar_sesion(sid) else err("No se pudo eliminar.")


# ══════════════════════════════════════════════════════════════════
#  Admin — Inscripciones
# ══════════════════════════════════════════════════════════════════

def menu_inscripciones():
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
            _ver_inscripciones_cohorte()
        elif op == "2":
            _ver_inscripciones_estudiante()
        elif op == "3":
            _inscribir_estudiante_admin()
        elif op == "4":
            _cancelar_inscripcion_admin()
        elif op == "5":
            _reactivar_inscripcion_admin()
        elif op == "6":
            _inscripciones_sin_pago()
        elif op == "7":
            break
        else:
            err("Opción inválida.")
        pausar()


def _ver_inscripciones_cohorte():
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
            f"[green]Activas: {activas}[/]  |  "
            f"[red]Canceladas: {canceladas}[/][/]"
        )


def _ver_inscripciones_estudiante():
    tabla_estudiantes(listar_estudiantes())
    est_id = pedir_int("ID de estudiante")
    if not est_id:
        return
    tabla_inscripciones(listar_inscripciones(estudiante_id=est_id))


def _inscribir_estudiante_admin():
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
    # Mostrar condiciones del curso si existen
    condiciones = obtener_condiciones_curso(cohorte["curso_id"])
    if condiciones:
        console.print(Panel(
            f"[yellow]{condiciones}[/]",
            title="[bold yellow]  Condiciones de inscripción  [/]",
            border_style="yellow",
            box=box.ROUNDED,
        ))
    if not cupo_disponible(coh_id):
        err("La cohorte no tiene cupo disponible.")
        return
    iid = inscribir_estudiante(est_id, coh_id)
    if iid:
        ok(f"Inscripción registrada con ID {iid}.")
    else:
        err("No se pudo inscribir. El estudiante puede ya estar inscripto en esta cohorte.")


def _cancelar_inscripcion_admin():
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


def _reactivar_inscripcion_admin():
    console.print(Panel("[bold cyan]REACTIVAR INSCRIPCIÓN[/]", box=box.ROUNDED, border_style="cyan"))
    tabla_cohortes(listar_cohortes(solo_activas=False))
    cohorte_id = pedir_int("ID de cohorte")
    if cohorte_id is None:
        return
    # Mostrar solo las canceladas
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


def _inscripciones_sin_pago():
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
    t.add_column("Tarifa", justify="right", min_width=10)
    t.add_column("Fecha inscr.", min_width=13)
    for p in pendientes:
        t.add_row(
            str(p["id"]), p["estudiante"], p["email"],
            p["cohorte"], p["curso"],
            f"[yellow]${p['tarifa_estudiante']:.2f}[/]",
            p["fecha_inscripcion"][:10],
        )
    console.print(t)
    console.print(f"\n  [bold yellow]  ⚠  {len(pendientes)} estudiante(s) sin pago registrado[/]")


# ══════════════════════════════════════════════════════════════════
#  Admin — Pagos
# ══════════════════════════════════════════════════════════════════

def menu_pagos():
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
            _registrar_pago_estudiante()
        elif op == "3":
            _pagos_de_cohorte()
        elif op == "4":
            _pagos_de_estudiante()
        elif op == "5":
            _anular_pago_estudiante()
        elif op == "7":
            _registrar_pago_docente()
        elif op == "8":
            _registrar_pago_materiales_docente()
        elif op == "9":
            tabla_pagos_docentes(listar_pagos_docente())
        elif op == "10":
            _pagos_pendientes_docentes()
        elif op == "11":
            _marcar_pago_docente_pagado()
        elif op == "12":
            _anular_pago_docente()
        elif op == "14":
            _resumen_cohorte()
        elif op == "15":
            break
        elif op in ("1", "6", "13"):
            pass  # separadores de sección
        else:
            err("Opción inválida.")
        pausar()


def _registrar_pago_estudiante():
    console.print(Panel("[bold cyan]REGISTRAR PAGO DE ESTUDIANTE[/]", box=box.ROUNDED, border_style="cyan"))
    tabla_cohortes(listar_cohortes(solo_activas=False))
    cohorte_id = pedir_int("ID de cohorte")
    if cohorte_id is None:
        return
    tabla_inscripciones(listar_inscripciones(cohorte_id=cohorte_id))
    insc_id = pedir_int("ID de inscripción")
    if insc_id is None:
        return
    monto = pedir_float("Monto")
    console.print("  Métodos: [cyan]efectivo[/], [cyan]transferencia[/], [cyan]tarjeta[/]")
    metodo = Prompt.ask("[white]  Método de pago[/]", default="efectivo").strip()
    obs = Prompt.ask("[white]  Observación (opcional)[/]", default="").strip()
    pid = registrar_pago_estudiante(insc_id, monto, metodo, obs)
    if pid:
        ok(f"Pago registrado con ID {pid}. Monto: ${monto:.2f}")


def _registrar_pago_docente():
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
        f"  [cyan]Monto calculado: ${monto_calc:.2f}[/]  "
        f"(tarifa [white]${docente['tarifa_hora']:.2f}[/]/h × [white]{horas}[/]h)"
    )
    obs = Prompt.ask("[white]  Observación (opcional)[/]", default="").strip()
    pid = registrar_pago_docente(did, coh_id, horas, obs)
    if pid:
        ok(f"Pago registrado con ID {pid}. Monto: ${monto_calc:.2f}")


def _registrar_pago_materiales_docente():
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
    monto = pedir_float("Monto a pagar")
    obs = Prompt.ask("[white]  Observación (opcional)[/]", default="").strip()
    pid = registrar_pago_materiales_docente(did, coh_id, monto, concepto, obs)
    if pid:
        ok(f"Pago por materiales registrado con ID {pid}. Monto: ${monto:.2f}")


def _pagos_de_cohorte():
    """Ver todos los pagos de estudiantes de una cohorte."""
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
            f"  [dim]Total cobrado: [green]${total:.2f}[/]"
            + (f"  |  Anulados: [red]{anulados}[/]" if anulados else "") + "[/]"
        )


def _pagos_de_estudiante():
    """Ver todos los pagos de un estudiante específico."""
    tabla_estudiantes(listar_estudiantes())
    est_id = pedir_int("ID de estudiante")
    if est_id is None:
        return
    pagos = listar_pagos_estudiante(estudiante_id=est_id)
    tabla_pagos_estudiantes(pagos)
    if pagos:
        total = sum(p["monto"] for p in pagos if p["estado"] != "anulado")
        console.print(f"  [dim]Total pagado (sin anulados): [green]${total:.2f}[/][/]")


def _anular_pago_estudiante():
    """Anula un pago de estudiante (lo marca como 'anulado')."""
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
    if Confirm.ask(
        f"[yellow]  ¿Confirma anular pago ${pago['monto']:.2f} de '{pago['estudiante']}'?[/]"
    ):
        ok("Pago anulado.") if anular_pago_estudiante(pid) else err("Error al anular.")


def _pagos_pendientes_docentes():
    """Muestra todos los pagos a docentes con estado pendiente."""
    pagos = listar_pagos_docente_pendientes()
    if not pagos:
        ok("No hay pagos pendientes de docentes.")
        return
    encabezado("PAGOS PENDIENTES — DOCENTES")
    tabla_pagos_docentes(pagos)
    total = sum(p["monto"] for p in pagos)
    console.print(f"\n  [bold yellow]  ⚠  Total pendiente: ${total:.2f}[/]")


def _marcar_pago_docente_pagado():
    """Cambia el estado de un pago a docente a 'pagado'."""
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
    if Confirm.ask(
        f"[yellow]  ¿Confirma marcar como pagado: ${pago['monto']:.2f} a '{pago['docente']}'?[/]"
    ):
        ok("Marcado como pagado.") if marcar_pago_docente_pagado(pid) else err("Error al actualizar.")


def _anular_pago_docente():
    """Anula un pago a docente."""
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
    if Confirm.ask(
        f"[yellow]  ¿Confirma anular pago ${pago['monto']:.2f} a '{pago['docente']}'?[/]"
    ):
        ok("Pago anulado.") if anular_pago_docente(pid) else err("Error al anular.")


def _resumen_cohorte():
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
    t.add_row("Recaudado de estudiantes", f"[green]${r['total_estudiantes']:.2f}[/]")
    t.add_row("Pagado a docentes",        f"[red]${r['total_docentes']:.2f}[/]")
    t.add_row("Balance",                  f"[{'green' if r['balance'] >= 0 else 'red'}]${r['balance']:.2f}[/]")
    console.print()
    console.print(Panel(
        t,
        title=f"[bold cyan]Resumen: {cohorte['nombre']} — {cohorte['curso']}[/]",
        border_style="cyan",
        box=box.ROUNDED,
    ))


# ══════════════════════════════════════════════════════════════════
#  Admin — Reportes
# ══════════════════════════════════════════════════════════════════

def menu_reportes():
    while True:
        limpiar()
        encabezado("REPORTES ACADÉMICOS Y ADMINISTRATIVOS")
        op = mostrar_menu("Reportes", [
            "Reporte de cursos",
            "Reporte de cohortes",
            "Reporte de participación de una cohorte",
            "Reporte de docentes",
            "Reporte financiero global",
            "Reporte de inscripciones por período",
            "Exportar reporte a CSV",
            "Volver",
        ])
        if op == "1":
            _reporte_cursos()
        elif op == "2":
            _reporte_cohortes()
        elif op == "3":
            _reporte_participacion()
        elif op == "4":
            _reporte_docentes()
        elif op == "5":
            _reporte_financiero()
        elif op == "6":
            _reporte_inscripciones()
        elif op == "7":
            _exportar_reporte()
        elif op == "8":
            break
        else:
            err("Opción inválida.")
        pausar()


def _reporte_cursos():
    datos = reporte_cursos()
    if not datos:
        warn("No hay cursos.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan", title="[bold]Cursos[/]")
    t.add_column("ID", style="dim", width=5)
    t.add_column("Curso", min_width=22)
    t.add_column("Modalidad", min_width=12)
    t.add_column("Horas", justify="right", width=7)
    t.add_column("Tarifa", justify="right", min_width=10)
    t.add_column("Cohortes", justify="right", width=9)
    t.add_column("Inscriptos", justify="right", width=10)
    t.add_column("Activo", justify="center", width=8)
    for d in datos:
        activo = "[green]Sí[/]" if d["activo"] else "[red]No[/]"
        t.add_row(
            str(d["id"]), d["curso"], d["modalidad"],
            str(d["horas_totales"]), f"[cyan]${d['tarifa_estudiante']:.2f}[/]",
            str(d["total_cohortes"]), f"[cyan]{d['total_inscriptos']}[/]",
            activo,
        )
    console.print(t)


def _reporte_cohortes():
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
    t.add_column("Ingresos", justify="right", min_width=10)
    t.add_column("Balance", justify="right", min_width=10)
    for d in datos:
        pct_color = "green" if d["ocupacion_pct"] >= 75 else ("yellow" if d["ocupacion_pct"] >= 40 else "red")
        bal_color = "green" if d["balance"] >= 0 else "red"
        t.add_row(
            str(d["id"]), d["cohorte"], d["curso"], d["modalidad"],
            f"{d['fecha_inicio']} → {d['fecha_fin']}",
            f"[{pct_color}]{d['ocupacion_pct']}%[/]",
            str(d["total_sesiones"]),
            f"[green]${d['ingresos_estudiantes']:.2f}[/]",
            f"[{bal_color}]${d['balance']:.2f}[/]",
        )
    console.print(t)


def _reporte_participacion():
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
    t.add_column("Email", min_width=22)
    t.add_column("Estado", min_width=10)
    t.add_column("Sesiones", justify="right", width=9)
    t.add_column("Presentes", justify="right", width=10)
    t.add_column("Asist.%", justify="right", width=9)
    t.add_column("Total pagado", justify="right", min_width=12)
    t.add_column("Aprobado", justify="center", width=10)
    for e in datos:
        pct = e["pct_asistencia"]
        pct_color = "green" if pct >= 75 else ("yellow" if pct >= 50 else "red")
        aprobado = "[green]Sí[/]" if e["aprobado"] else "[red]No[/]"
        estado_color = "green" if e["estado_inscripcion"] == "activa" else "red"
        t.add_row(
            e["estudiante"], e["email"],
            f"[{estado_color}]{e['estado_inscripcion']}[/]",
            str(e["total_sesiones"]),
            str(e["presentes"]),
            f"[{pct_color}]{pct}%[/]",
            f"[cyan]${e['total_pagado']:.2f}[/]",
            aprobado,
        )
    console.print(t)


def _reporte_docentes():
    datos = reporte_docentes()
    if not datos:
        warn("No hay docentes.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan", title="[bold]Actividad de Docentes[/]")
    t.add_column("Docente", min_width=22)
    t.add_column("Especialidad", min_width=16)
    t.add_column("Tarifa/h", justify="right", min_width=9)
    t.add_column("Cohortes", justify="right", width=9)
    t.add_column("Hs dictadas", justify="right", width=12)
    t.add_column("Total cobrado", justify="right", min_width=13)
    for d in datos:
        t.add_row(
            d["docente"], d["especialidad"] or "",
            f"[cyan]${d['tarifa_hora']:.2f}[/]",
            str(d["cohortes_asignadas"]),
            f"{d['horas_dictadas_sesiones']:.1f}h",
            f"[green]${d['total_cobrado']:.2f}[/]",
        )
    console.print(t)


def _reporte_financiero():
    r = reporte_financiero_global()
    moneda = obtener_config("moneda") or "USD"
    bal_color = "green" if r["balance"] >= 0 else "red"

    # Panel resumen
    resumen = Table(box=box.DOUBLE_EDGE, border_style="cyan", show_header=False, padding=(0, 3))
    resumen.add_column("Concepto", style="white")
    resumen.add_column("Monto", style="bold", justify="right")
    resumen.add_row("Ingresos (estudiantes)",   f"[green]${r['total_ingresos']:.2f} {moneda}[/]")
    resumen.add_row("Egresos (docentes)",        f"[red]${r['total_egresos']:.2f} {moneda}[/]")
    resumen.add_row("Balance",                   f"[{bal_color}]${r['balance']:.2f} {moneda}[/]")
    resumen.add_row("Pagos pendientes docentes", f"[yellow]${r['pagos_pendientes_docentes']:.2f} {moneda}[/]")
    console.print()
    console.print(Panel(resumen, title="[bold cyan]Resumen Financiero Global[/]", border_style="cyan", box=box.ROUNDED))

    # Ingresos por modalidad
    if r["ingresos_por_modalidad"]:
        console.print()
        tm = Table(box=box.SIMPLE, header_style="bold cyan", title="[cyan]Ingresos por modalidad[/]")
        tm.add_column("Modalidad"); tm.add_column("Pagos", justify="right"); tm.add_column("Total", justify="right")
        for m in r["ingresos_por_modalidad"]:
            tm.add_row(m["modalidad"], str(m["cantidad_pagos"]), f"[green]${m['total']:.2f}[/]")
        console.print(tm)

    # Egresos por tipo
    if r["egresos_por_tipo"]:
        console.print()
        te = Table(box=box.SIMPLE, header_style="bold cyan", title="[cyan]Egresos por tipo de pago[/]")
        te.add_column("Tipo"); te.add_column("Pagos", justify="right"); te.add_column("Total", justify="right")
        for e in r["egresos_por_tipo"]:
            te.add_row(e["tipo"].capitalize(), str(e["cantidad_pagos"]), f"[red]${e['total']:.2f}[/]")
        console.print(te)


def _reporte_inscripciones():
    anio_str = Prompt.ask("[white]  Año a consultar (Enter = todos)[/]", default="").strip()
    anio = anio_str if anio_str and anio_str.isdigit() else None
    datos = reporte_inscripciones_periodo(anio)
    if not datos:
        warn("Sin datos de inscripciones.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan",
              title=f"[bold]Inscripciones {'— ' + anio if anio else '(todos los años)'}[/]")
    t.add_column("Mes", min_width=8)
    t.add_column("Curso", min_width=22)
    t.add_column("Modalidad", min_width=11)
    t.add_column("Inscriptos", justify="right", min_width=10)
    t.add_column("Canceladas", justify="right", min_width=10)
    for d in datos:
        t.add_row(
            d["mes"], d["curso"], d["modalidad"],
            f"[cyan]{d['inscriptos']}[/]", f"[red]{d['canceladas']}[/]",
        )
    console.print(t)


def _exportar_reporte():
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


# ══════════════════════════════════════════════════════════════════
#  Admin — Configuración del sistema
# ══════════════════════════════════════════════════════════════════

def menu_configuracion():
    while True:
        limpiar()
        encabezado("CONFIGURACIÓN DEL SISTEMA", "Parámetros parametrizables")
        op = mostrar_menu("Configuración", [
            "Ver parámetros del sistema",
            "Editar parámetro",
            "Gestionar modalidades de cursado",
            "Gestionar roles de usuario",
            "Condiciones de inscripción por curso",
            "Volver",
        ])
        if op == "1":
            _ver_configuracion()
        elif op == "2":
            _editar_configuracion()
        elif op == "3":
            _menu_modalidades()
        elif op == "4":
            _menu_roles()
        elif op == "5":
            _menu_condiciones_inscripcion()
        elif op == "6":
            break
        else:
            err("Opción inválida.")
        pausar()


def _ver_configuracion():
    configs = listar_config()
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan",
              title="[bold]Parámetros del Sistema[/]")
    t.add_column("Parámetro (clave)", min_width=30)
    t.add_column("Valor", min_width=20)
    t.add_column("Descripción")
    for c in configs:
        t.add_row(c["clave"], f"[cyan]{c['valor']}[/]", c["descripcion"] or "")
    console.print(t)


def _editar_configuracion():
    _ver_configuracion()
    clave = Prompt.ask("[white]  Clave a editar[/]").strip()
    if not clave:
        return
    nuevo_valor = Prompt.ask("[white]  Nuevo valor[/]").strip()
    if actualizar_config(clave, nuevo_valor):
        ok(f"Parámetro '{clave}' actualizado a '{nuevo_valor}'.")
    else:
        err("Clave no encontrada.")


def _menu_modalidades():
    while True:
        limpiar()
        encabezado("MODALIDADES DE CURSADO")
        op = mostrar_menu("Modalidades", [
            "Ver modalidades", "Agregar modalidad", "Editar modalidad", "Volver",
        ])
        if op == "1":
            modalidades = cfg_listar_modalidades()
            t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
            t.add_column("ID", width=5); t.add_column("Nombre"); t.add_column("Descripción")
            for m in modalidades:
                t.add_row(str(m["id"]), m["nombre"], m["descripcion"] or "")
            console.print(t)
        elif op == "2":
            nombre = Prompt.ask("[white]  Nombre de la modalidad[/]").strip()
            desc = Prompt.ask("[white]  Descripción[/]", default="").strip()
            mid = agregar_modalidad(nombre, desc)
            ok(f"Modalidad '{nombre}' creada con ID {mid}.") if mid else err("Ya existe esa modalidad.")
        elif op == "3":
            mid = pedir_int("ID a editar")
            if mid is None:
                pausar()
                continue
            nombre = Prompt.ask("[white]  Nuevo nombre (Enter = sin cambio)[/]", default="").strip() or None
            desc = Prompt.ask("[white]  Nueva descripción (Enter = sin cambio)[/]", default="").strip() or None
            ok("Actualizada.") if actualizar_modalidad(mid, nombre, desc) else err("No encontrada.")
        elif op == "4":
            break
        else:
            err("Opción inválida.")
        pausar()


def _menu_roles():
    limpiar()
    encabezado("ROLES DE USUARIO")
    roles = listar_roles()
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("ID", width=5); t.add_column("Rol"); t.add_column("Descripción")
    for r in roles:
        t.add_row(str(r["id"]), r["nombre"], r["descripcion"] or "")
    console.print(t)
    if Confirm.ask("[yellow]  ¿Desea agregar un nuevo rol?[/]", default=False):
        nombre = Prompt.ask("[white]  Nombre del rol[/]").strip()
        desc = Prompt.ask("[white]  Descripción[/]", default="").strip()
        rid = agregar_rol(nombre, desc)
        ok(f"Rol '{nombre}' creado con ID {rid}.") if rid else err("Ya existe ese rol.")


def _menu_condiciones_inscripcion():
    limpiar()
    encabezado("CONDICIONES DE INSCRIPCIÓN POR CURSO")
    tabla_cursos(listar_cursos(solo_activos=False))
    cid = pedir_int("ID de curso")
    if cid is None:
        return
    curso = obtener_curso(cid)
    if not curso:
        err("Curso no encontrado.")
        return
    cond_actual = obtener_condiciones_curso(cid)
    console.print(Panel(
        f"[white]Condiciones actuales:[/]\n{cond_actual or '[dim]Sin condiciones definidas[/]'}",
        title=f"[bold cyan]{curso['nombre']}[/]",
        border_style="cyan",
        box=box.ROUNDED,
    ))
    console.print("  [dim]Ingrese las condiciones de inscripción (texto libre).[/]")
    console.print("  [dim]Ej: Requiere secundario completo. Edad mínima: 18 años.[/]")
    nuevas = Prompt.ask("[white]  Nuevas condiciones (Enter = sin cambios)[/]", default="").strip()
    if nuevas:
        actualizar_condiciones_curso(cid, nuevas)
        ok("Condiciones actualizadas.")


# ══════════════════════════════════════════════════════════════════
#  Admin — Asistencias
# ══════════════════════════════════════════════════════════════════

def menu_asistencias():
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
            _registrar_asistencia_sesion()
        elif op == "2":
            _ver_asistencia_sesion()
        elif op == "3":
            _resumen_asistencia_cohorte()
        elif op == "4":
            _historial_asistencia_estudiante()
        elif op == "5":
            _exportar_asistencia_csv()
        elif op == "6":
            break
        else:
            err("Opción inválida.")
        pausar()


def _seleccionar_sesion():
    """Helper: muestra cohortes → sesiones y retorna sesion_id."""
    tabla_cohortes(listar_cohortes(solo_activas=False))
    cohorte_id = pedir_int("ID de cohorte")
    if cohorte_id is None:
        return None, None
    sesiones = listar_sesiones(cohorte_id)
    tabla_sesiones(sesiones)
    sesion_id = pedir_int("ID de sesión")
    return sesion_id, cohorte_id


def _registrar_asistencia_sesion():
    console.print(Panel("[bold cyan]REGISTRAR ASISTENCIA[/]", box=box.ROUNDED, border_style="cyan"))
    sesion_id, _ = _seleccionar_sesion()
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
            choices=["P", "p", "A", "a", ""],
            default="",
            show_choices=False,
        ).strip().upper()
        if resp == "P":
            registrar_asistencia(sesion_id, r["estudiante_id"], presente=1)
            cambios += 1
        elif resp == "A":
            registrar_asistencia(sesion_id, r["estudiante_id"], presente=0)
            cambios += 1
    ok(f"Asistencia guardada. {cambios} registro(s) actualizados.")


def _ver_asistencia_sesion():
    sesion_id, _ = _seleccionar_sesion()
    if sesion_id is None:
        return
    tabla_asistencia_sesion(listar_asistencia_sesion(sesion_id))


def _resumen_asistencia_cohorte():
    tabla_cohortes(listar_cohortes(solo_activas=False))
    cohorte_id = pedir_int("ID de cohorte")
    if cohorte_id is None:
        return
    cohorte = obtener_cohorte(cohorte_id)
    if not cohorte:
        err("Cohorte no encontrada.")
        return
    resumen = resumen_asistencia_cohorte(cohorte_id)
    encabezado(f"Asistencia: {cohorte['nombre']} — {cohorte['curso']}")
    tabla_resumen_asistencia(resumen)


def _historial_asistencia_estudiante():
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
        t.add_row(
            r["fecha"],
            f"{r['hora_inicio']}–{r['hora_fin']}",
            r["cohorte"],
            r["tema"] or "",
            estado,
        )
    console.print(t)


def _exportar_asistencia_csv():
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


# ══════════════════════════════════════════════════════════════════
#  Menú principal de Administrador
# ══════════════════════════════════════════════════════════════════

def menu_admin(usuario):
    while True:
        limpiar()
        encabezado("PANEL DE ADMINISTRADOR", f"Usuario: {usuario['nombre']} {usuario['apellido']}")
        op = mostrar_menu("Menú Administrador", [
            "Gestión de usuarios",
            "Gestión de estudiantes",
            "Gestión de docentes",
            "Gestión de cursos",
            "Gestión de cohortes",
            "Gestión de inscripciones",
            "Gestión de pagos",
            "Gestión de asistencias",
            "Reportes académicos y administrativos",
            "Configuración del sistema",
            "Cerrar sesión",
        ])
        if op == "1":
            menu_usuarios()
        elif op == "2":
            menu_estudiantes()
        elif op == "3":
            menu_docentes()
        elif op == "4":
            menu_cursos()
        elif op == "5":
            menu_cohortes()
        elif op == "6":
            menu_inscripciones()
        elif op == "7":
            menu_pagos()
        elif op == "8":
            menu_asistencias()
        elif op == "9":
            menu_reportes()
        elif op == "10":
            menu_configuracion()
        elif op == "11":
            ok("Sesión cerrada.")
            pausar()
            break
        else:
            err("Opción inválida.")
            pausar()


# ══════════════════════════════════════════════════════════════════
#  Portal del Docente
# ══════════════════════════════════════════════════════════════════

def menu_docente(usuario):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM docentes WHERE usuario_id = ?", (usuario["id"],))
    row = cursor.fetchone()
    conn.close()
    if not row:
        err("No se encontró el perfil de docente.")
        pausar()
        return
    docente_id = row["id"]

    while True:
        limpiar()
        encabezado("PORTAL DEL DOCENTE", f"{usuario['nombre']} {usuario['apellido']}")
        op = mostrar_menu("Menú Docente", [
            "Mis datos",
            "Mis cohortes y sesiones",
            "Registrar asistencia de una sesión",
            "Mis pagos",
            "Cerrar sesión",
        ])
        if op == "1":
            _datos_docente(docente_id)
        elif op == "2":
            _sesiones_docente(docente_id)
        elif op == "3":
            _registrar_asistencia_docente(docente_id)
        elif op == "4":
            pagos = listar_pagos_docente(docente_id=docente_id)
            tabla_pagos_docentes(pagos)
            if pagos:
                total = sum(p["monto"] for p in pagos)
                console.print(f"\n  [bold cyan]Total recibido: ${total:.2f}[/]")
        elif op == "5":
            ok("Sesión cerrada.")
            pausar()
            break
        else:
            err("Opción inválida.")
        pausar()


def _datos_docente(docente_id):
    d = obtener_docente(docente_id)
    if not d:
        return
    console.print(Panel(
        f"[white]Nombre:[/]       [cyan]{d['nombre']} {d['apellido']}[/]\n"
        f"[white]Email:[/]        [cyan]{d['email']}[/]\n"
        f"[white]Especialidad:[/] [cyan]{d['especialidad'] or 'N/A'}[/]\n"
        f"[white]Tarifa/hora:[/]  [cyan]${d['tarifa_hora']:.2f}[/]",
        title="[bold cyan]Mis Datos[/]",
        border_style="cyan",
        box=box.ROUNDED,
    ))


def _sesiones_docente(docente_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT co.id, co.nombre as cohorte, c.nombre as curso,
               co.fecha_inicio, co.fecha_fin
        FROM sesiones s
        JOIN cohortes co ON s.cohorte_id = co.id
        JOIN cursos c ON co.curso_id = c.id
        WHERE s.docente_id = ?
        ORDER BY co.fecha_inicio DESC
    """, (docente_id,))
    cohortes = [dict(r) for r in cursor.fetchall()]
    conn.close()
    if not cohortes:
        warn("No tenés sesiones registradas.")
        return
    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("ID", width=5)
    t.add_column("Cohorte", min_width=15)
    t.add_column("Curso", min_width=20)
    t.add_column("Inicio", min_width=12)
    t.add_column("Fin", min_width=12)
    for co in cohortes:
        t.add_row(str(co["id"]), co["cohorte"], co["curso"], co["fecha_inicio"], co["fecha_fin"])
    console.print(t)
    coh_str = Prompt.ask("[white]  Ver sesiones de cohorte ID (Enter = omitir)[/]", default="").strip()
    if coh_str:
        try:
            tabla_sesiones(listar_sesiones(int(coh_str)))
        except ValueError:
            pass


def _registrar_asistencia_docente(docente_id):
    """El docente registra asistencia de sus propias sesiones."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, s.fecha, s.hora_inicio, s.hora_fin, s.tema,
               co.nombre as cohorte, c.nombre as curso
        FROM sesiones s
        JOIN cohortes co ON s.cohorte_id = co.id
        JOIN cursos c ON co.curso_id = c.id
        WHERE s.docente_id = ?
        ORDER BY s.fecha DESC, s.hora_inicio DESC
    """, (docente_id,))
    mis_sesiones = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not mis_sesiones:
        warn("No tenés sesiones registradas.")
        return

    t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("ID", width=5)
    t.add_column("Fecha", min_width=12)
    t.add_column("Horario", min_width=14)
    t.add_column("Cohorte", min_width=14)
    t.add_column("Tema")
    for s in mis_sesiones:
        t.add_row(
            str(s["id"]), s["fecha"],
            f"{s['hora_inicio']}–{s['hora_fin']}",
            s["cohorte"], s["tema"] or "",
        )
    console.print(t)

    sesion_id = pedir_int("ID de sesión a tomar asistencia")
    if sesion_id is None:
        return
    # Verificar que la sesión pertenece al docente
    sesion_ids = [s["id"] for s in mis_sesiones]
    if sesion_id not in sesion_ids:
        err("Sesión no encontrada entre tus sesiones.")
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
            choices=["P", "p", "A", "a", ""],
            default="",
            show_choices=False,
        ).strip().upper()
        if resp == "P":
            registrar_asistencia(sesion_id, r["estudiante_id"], presente=1)
            cambios += 1
        elif resp == "A":
            registrar_asistencia(sesion_id, r["estudiante_id"], presente=0)
            cambios += 1
    ok(f"Asistencia guardada. {cambios} registro(s) actualizados.")


# ══════════════════════════════════════════════════════════════════
#  Portal del Estudiante
# ══════════════════════════════════════════════════════════════════

def menu_estudiante(usuario):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM estudiantes WHERE usuario_id = ?", (usuario["id"],))
    row = cursor.fetchone()
    conn.close()
    if not row:
        err("No se encontró el perfil de estudiante.")
        pausar()
        return
    estudiante_id = row["id"]

    while True:
        limpiar()
        encabezado("PORTAL DEL ESTUDIANTE", f"{usuario['nombre']} {usuario['apellido']}")
        op = mostrar_menu("Menú Estudiante", [
            "Mis datos",
            "Mis inscripciones",
            "Inscribirme en una cohorte",
            "Mis pagos",
            "Mi asistencia",
            "Cerrar sesión",
        ])
        if op == "1":
            _datos_estudiante(estudiante_id)
        elif op == "2":
            tabla_inscripciones(listar_inscripciones(estudiante_id=estudiante_id))
        elif op == "3":
            _inscribirse(estudiante_id)
        elif op == "4":
            inscripciones = listar_inscripciones(estudiante_id=estudiante_id)
            pagos = []
            for insc in inscripciones:
                pagos.extend(listar_pagos_estudiante(inscripcion_id=insc["id"]))
            tabla_pagos_estudiantes(pagos)
            if pagos:
                total = sum(p["monto"] for p in pagos)
                console.print(f"\n  [bold cyan]Total pagado: ${total:.2f}[/]")
        elif op == "5":
            _mi_asistencia(estudiante_id)
        elif op == "6":
            ok("Sesión cerrada.")
            pausar()
            break
        else:
            err("Opción inválida.")
        pausar()


def _datos_estudiante(estudiante_id):
    e = obtener_estudiante(estudiante_id)
    if not e:
        return
    console.print(Panel(
        f"[white]Nombre:[/]    [cyan]{e['nombre']} {e['apellido']}[/]\n"
        f"[white]Email:[/]     [cyan]{e['email']}[/]\n"
        f"[white]Documento:[/] [cyan]{e['documento'] or 'N/A'}[/]\n"
        f"[white]Teléfono:[/]  [cyan]{e['telefono'] or 'N/A'}[/]",
        title="[bold cyan]Mis Datos[/]",
        border_style="cyan",
        box=box.ROUNDED,
    ))


def _inscribirse(estudiante_id):
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
    # Mostrar condiciones de ingreso si existen
    condiciones = obtener_condiciones_curso(cohorte["curso_id"])
    if condiciones:
        console.print(Panel(
            f"[yellow]{condiciones}[/]",
            title="[bold yellow]  Condiciones de inscripción  [/]",
            border_style="yellow",
            box=box.ROUNDED,
        ))
        if not Confirm.ask("[yellow]  ¿Cumple con las condiciones de inscripción?[/]"):
            warn("Inscripción cancelada.")
            return
    console.print(
        f"\n  [white]Curso:[/] [cyan]{cohorte['curso']}[/]  |  "
        f"[white]Cohorte:[/] [cyan]{cohorte['nombre']}[/]  |  "
        f"[white]Período:[/] [cyan]{cohorte['fecha_inicio']} → {cohorte['fecha_fin']}[/]"
    )
    if Confirm.ask("[yellow]  ¿Confirma inscripción?[/]"):
        iid = inscribir_estudiante(estudiante_id, coh_id)
        if iid:
            ok(f"Inscripción realizada con ID {iid}.")


def _mi_asistencia(estudiante_id):
    historial = listar_asistencia_estudiante(estudiante_id)
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
        title="[bold cyan]Mi Asistencia General[/]",
        border_style="cyan",
        box=box.ROUNDED,
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
        t.add_row(
            r["fecha"],
            f"{r['hora_inicio']}–{r['hora_fin']}",
            r["cohorte"],
            r["tema"] or "",
            estado,
        )
    console.print(t)


# ══════════════════════════════════════════════════════════════════
#  Arranque
# ══════════════════════════════════════════════════════════════════

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


def main():
    inicializar_db()
    _crear_admin_inicial()

    while True:
        limpiar()
        encabezado("PLATAFORMA DE GESTIÓN ACADÉMICA", "Sistema de administración educativa")
        op = mostrar_menu("Menú Principal", ["Iniciar sesión", "Salir"])
        if op == "1":
            usuario = pantalla_login()
            if usuario:
                rol = usuario["rol"]
                if rol == "admin":
                    menu_admin(usuario)
                elif rol == "docente":
                    menu_docente(usuario)
                elif rol == "estudiante":
                    menu_estudiante(usuario)
                else:
                    warn(f"Módulo para rol '{rol}' no disponible.")
                    pausar()
        elif op == "2":
            limpiar()
            console.print(Panel(
                Align.center(Text("¡Hasta luego!", style="bold cyan")),
                box=box.ROUNDED,
                border_style="cyan",
                width=40,
                padding=(1, 0),
            ))
            console.print()
            break
        else:
            err("Opción inválida.")
            pausar()


if __name__ == "__main__":
    main()
