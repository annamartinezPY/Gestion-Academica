from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import box
from database import get_connection
from ui.helpers import console, limpiar, encabezado, ok, err, warn, mostrar_menu, pausar, pedir_int
from ui.tables import tabla_sesiones, tabla_pagos_docentes, tabla_asistencia_sesion
from controllers.docente_controller import obtener_docente
from controllers.cohorte_controller import listar_sesiones
from controllers.pago_controller import listar_pagos_docente
from controllers.asistencia_controller import registrar_asistencia, listar_asistencia_sesion


class PortalDocente:

    def __init__(self, usuario):
        self.usuario = usuario
        self.docente_id = self._obtener_docente_id()

    def _obtener_docente_id(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM docentes WHERE usuario_id = ?", (self.usuario["id"],))
        row = cursor.fetchone()
        conn.close()
        return row["id"] if row else None

    def mostrar(self):
        if not self.docente_id:
            err("No se encontró el perfil de docente.")
            pausar()
            return
        while True:
            limpiar()
            encabezado("PORTAL DEL DOCENTE",
                       f"{self.usuario['nombre']} {self.usuario['apellido']}")
            op = mostrar_menu("Menú Docente", [
                "Mis datos", "Mis cohortes y sesiones",
                "Registrar asistencia de una sesión", "Mis pagos", "Cerrar sesión",
            ])
            if op == "1":
                self._mis_datos()
            elif op == "2":
                self._mis_sesiones()
            elif op == "3":
                self._registrar_asistencia()
            elif op == "4":
                self._mis_pagos()
            elif op == "5":
                ok("Sesión cerrada.")
                pausar()
                break
            else:
                err("Opción inválida.")
            pausar()

    def _mis_datos(self):
        d = obtener_docente(self.docente_id)
        if not d:
            return
        tarifa = f"₲ {int(d['tarifa_hora']):,}".replace(",", ".")
        console.print(Panel(
            f"[white]Nombre:[/]       [cyan]{d['nombre']} {d['apellido']}[/]\n"
            f"[white]Email:[/]        [cyan]{d['email']}[/]\n"
            f"[white]Especialidad:[/] [cyan]{d['especialidad'] or 'N/A'}[/]\n"
            f"[white]Tarifa/hora:[/]  [cyan]{tarifa}[/]",
            title="[bold cyan]Mis Datos[/]", border_style="cyan", box=box.ROUNDED,
        ))

    def _mis_sesiones(self):
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
        """, (self.docente_id,))
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

    def _registrar_asistencia(self):
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
        """, (self.docente_id,))
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
            t.add_row(str(s["id"]), s["fecha"],
                      f"{s['hora_inicio']}–{s['hora_fin']}", s["cohorte"], s["tema"] or "")
        console.print(t)
        sesion_id = pedir_int("ID de sesión a tomar asistencia")
        if sesion_id is None:
            return
        if sesion_id not in [s["id"] for s in mis_sesiones]:
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
                choices=["P", "p", "A", "a", ""], default="", show_choices=False,
            ).strip().upper()
            if resp == "P":
                registrar_asistencia(sesion_id, r["estudiante_id"], presente=1)
                cambios += 1
            elif resp == "A":
                registrar_asistencia(sesion_id, r["estudiante_id"], presente=0)
                cambios += 1
        ok(f"Asistencia guardada. {cambios} registro(s) actualizados.")

    def _mis_pagos(self):
        pagos = listar_pagos_docente(docente_id=self.docente_id)
        tabla_pagos_docentes(pagos)
        if pagos:
            total = sum(p["monto"] for p in pagos)
            console.print(f"\n  [bold cyan]Total recibido: ₲ {int(total):,}[/]".replace(",", "."))
