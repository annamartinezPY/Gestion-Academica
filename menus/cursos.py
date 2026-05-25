from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from ui.helpers import console, limpiar, encabezado, ok, err, mostrar_menu, pausar, pedir_int
from ui.tables import tabla_cursos
from controllers.curso_controller import (
    registrar_curso, listar_cursos, obtener_curso,
    actualizar_curso, desactivar_curso, listar_modalidades,
)


class MenuCursos:

    def mostrar(self):
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
                self._registrar()
            elif op == "3":
                self._actualizar()
            elif op == "4":
                self._desactivar()
            elif op == "5":
                break
            else:
                err("Opción inválida.")
            pausar()

    def _registrar(self):
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
        tarifa_str = Prompt.ask("[white]  Tarifa para estudiantes (₲)[/]", default="0")
        try:
            horas = int(horas_str)
            tarifa = float(tarifa_str)
        except ValueError:
            err("Valores numéricos inválidos.")
            return
        cid = registrar_curso(nombre, descripcion, modalidad_id, horas, tarifa)
        if cid:
            ok(f"Curso registrado con ID {cid}.")

    def _actualizar(self):
        tabla_cursos(listar_cursos(solo_activos=False))
        cid = pedir_int("ID a actualizar")
        if cid is None:
            return
        nombre = Prompt.ask("[white]  Nuevo nombre (Enter = sin cambio)[/]", default="").strip() or None
        descripcion = Prompt.ask("[white]  Nueva descripción (Enter = sin cambio)[/]", default="").strip() or None
        horas_str = Prompt.ask("[white]  Nuevas horas totales (Enter = sin cambio)[/]", default="").strip()
        tarifa_str = Prompt.ask("[white]  Nueva tarifa ₲ (Enter = sin cambio)[/]", default="").strip()
        horas = int(horas_str) if horas_str else None
        tarifa = float(tarifa_str) if tarifa_str else None
        if actualizar_curso(cid, nombre, descripcion, horas_totales=horas, tarifa_estudiante=tarifa):
            ok("Curso actualizado.")

    def _desactivar(self):
        tabla_cursos(listar_cursos(solo_activos=False))
        cid = pedir_int("ID a desactivar")
        if cid is None:
            return
        if Confirm.ask(f"[yellow]  ¿Confirma desactivar curso {cid}?[/]"):
            ok("Desactivado.") if desactivar_curso(cid) else err("No encontrado.")
