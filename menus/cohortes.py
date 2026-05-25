import re
import re
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from ui.helpers import console, limpiar, encabezado, ok, err, warn, mostrar_menu, pausar, pedir_int, pedir_fecha
from ui.tables import tabla_cohortes, tabla_sesiones, tabla_cursos, tabla_docentes
from controllers.cohorte_controller import (
    registrar_cohorte, listar_cohortes, obtener_cohorte, actualizar_cohorte,
    registrar_sesion, listar_sesiones, desactivar_cohorte,
    obtener_sesion, actualizar_sesion, eliminar_sesion, contar_inscriptos,
)
from controllers.curso_controller import listar_cursos, obtener_curso
from controllers.docente_controller import listar_docentes
from controllers.institucion_controller import listar_instituciones

DIAS_SEMANA = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']


class MenuCohortes:

    def mostrar(self):
        while True:
            limpiar()
            encabezado("GESTIÓN DE COHORTES")
            op = mostrar_menu("Cohortes", [
                "Listar todas las cohortes", "Registrar cohorte",
                "Actualizar cohorte", "Desactivar cohorte",
                "Cohortes de un curso", "Registrar sesión de clase",
                "Ver sesiones de una cohorte", "Editar sesión",
                "Eliminar sesión", "Volver",
            ])
            if op == "1":
                tabla_cohortes(listar_cohortes(solo_activas=False))
            elif op == "2":
                self._registrar()
            elif op == "3":
                self._actualizar()
            elif op == "4":
                self._desactivar()
            elif op == "5":
                self._cohortes_de_curso()
            elif op == "6":
                self._registrar_sesion()
            elif op == "7":
                self._ver_sesiones()
            elif op == "8":
                self._editar_sesion()
            elif op == "9":
                self._eliminar_sesion()
            elif op == "10":
                break
            else:
                err("Opción inválida.")
            pausar()

    def _registrar(self):
        console.print(Panel("[bold cyan]REGISTRAR COHORTE[/]", box=box.ROUNDED, border_style="cyan"))
        # Paso 1: seleccionar institución para filtrar cursos
        instituciones = listar_instituciones(solo_activas=True)
        t_inst = Table(box=box.SIMPLE, header_style="bold cyan")
        t_inst.add_column("ID", width=5); t_inst.add_column("Institución"); t_inst.add_column("Modalidades")
        for i in instituciones:
            t_inst.add_row(str(i["id"]), i["nombre"], i["modalidades"] or "—")
        if instituciones:
            console.print(t_inst)
        inst_id_str = Prompt.ask(
            "[white]  ID de institución para filtrar cursos (Enter = todos)[/]", default=""
        ).strip()

        # Filtrar cursos por institución si se seleccionó
        todos_cursos = listar_cursos(solo_activos=True)
        if inst_id_str:
            try:
                inst_id = int(inst_id_str)
                cursos_filtrados = [c for c in todos_cursos if c.get("institucion_id") == inst_id]
            except ValueError:
                cursos_filtrados = todos_cursos
        else:
            cursos_filtrados = todos_cursos

        if not cursos_filtrados:
            warn("No hay cursos activos para esa institución.")
            return
        tabla_cursos(cursos_filtrados)

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

        # Días de clase
        console.print("\n  [dim]Días disponibles:[/]")
        for i, d in enumerate(DIAS_SEMANA, 1):
            console.print(f"    [{i}] {d}")
        dias_str = Prompt.ask(
            "[white]  Números de días separados por coma (ej: 1,3,5 = Lun/Mié/Vie) [opcional][/]",
            default=""
        ).strip()
        dias_clase = ""
        if dias_str:
            try:
                indices = [int(x.strip()) - 1 for x in dias_str.split(",")]
                dias_clase = ",".join(DIAS_SEMANA[i] for i in indices if 0 <= i < len(DIAS_SEMANA))
            except (ValueError, IndexError):
                warn("Días inválidos, se omite el campo.")

        carga_str = Prompt.ask("[white]  Carga horaria diaria en horas (ej: 2.5)[/]", default="0").strip()
        try:
            carga = float(carga_str)
        except ValueError:
            carga = 0.0

        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cohortes (nombre, curso_id, fecha_inicio, fecha_fin, cupo_maximo,
                                  dias_clase, carga_horaria_diaria, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (nombre, curso_id, fecha_inicio, fecha_fin, cupo, dias_clase or None, carga))
        conn.commit()
        coid = cursor.lastrowid
        conn.close()
        if coid:
            resumen = f"  Días: [cyan]{dias_clase or '—'}[/]  |  Carga: [cyan]{carga}h/día[/]"
            ok(f"Cohorte '{nombre}' registrada con ID {coid} para '{curso['nombre']}'.")
            console.print(resumen)

    def _actualizar(self):
        tabla_cohortes(listar_cohortes(solo_activas=False))
        coid = pedir_int("ID de cohorte a actualizar")
        if coid is None:
            return
        cohorte = obtener_cohorte(coid)
        if not cohorte:
            err("Cohorte no encontrada.")
            return
        nombre = Prompt.ask(f"[white]  Nombre (Enter = [dim]{cohorte['nombre']}[/])[/]", default="").strip() or None
        fecha_inicio_str = Prompt.ask(f"[white]  Fecha inicio (Enter = [dim]{cohorte['fecha_inicio']}[/])[/]", default="").strip()
        fecha_fin_str = Prompt.ask(f"[white]  Fecha fin (Enter = [dim]{cohorte['fecha_fin']}[/])[/]", default="").strip()
        cupo_str = Prompt.ask(f"[white]  Cupo máximo (Enter = [dim]{cohorte['cupo_maximo']}[/])[/]", default="").strip()
        if fecha_inicio_str and not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha_inicio_str):
            err("Formato de fecha inválido. Use YYYY-MM-DD.")
            return
        if fecha_fin_str and not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha_fin_str):
            err("Formato de fecha inválido. Use YYYY-MM-DD.")
            return
        cupo = int(cupo_str) if cupo_str else None
        if actualizar_cohorte(coid, nombre, fecha_inicio_str or None, fecha_fin_str or None, cupo):
            ok("Cohorte actualizada.")
        else:
            err("No se pudo actualizar.")

    def _cohortes_de_curso(self):
        tabla_cursos(listar_cursos(solo_activos=False))
        cid = pedir_int("ID del curso")
        if cid is None:
            return
        tabla_cohortes(listar_cohortes(curso_id=cid, solo_activas=False))

    def _registrar_sesion(self):
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

    def _ver_sesiones(self):
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

    def _desactivar(self):
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

    def _editar_sesion(self):
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
        tabla_docentes(listar_docentes())
        did_str = Prompt.ask(f"[white]  Nuevo docente ID (Enter = [dim]{sesion['docente_id']}[/])[/]", default="").strip()
        nuevo_did = int(did_str) if did_str else None
        fecha_str = Prompt.ask(f"[white]  Nueva fecha (Enter = [dim]{sesion['fecha']}[/])[/]", default="").strip()
        if fecha_str and not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha_str):
            err("Formato de fecha inválido.")
            return
        hi_str = Prompt.ask(f"[white]  Hora inicio (Enter = [dim]{sesion['hora_inicio']}[/])[/]", default="").strip()
        hf_str = Prompt.ask(f"[white]  Hora fin (Enter = [dim]{sesion['hora_fin']}[/])[/]", default="").strip()
        tema_str = Prompt.ask(f"[white]  Tema (Enter = [dim]{sesion['tema'] or 'vacío'}[/])[/]", default="").strip()
        if actualizar_sesion(sid, docente_id=nuevo_did, fecha=fecha_str or None,
                              hora_inicio=hi_str or None, hora_fin=hf_str or None, tema=tema_str or None):
            ok("Sesión actualizada.")
        else:
            err("No se pudo actualizar.")

    def _eliminar_sesion(self):
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
