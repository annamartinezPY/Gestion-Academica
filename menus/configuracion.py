from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box
from ui.helpers import console, limpiar, encabezado, ok, err, mostrar_menu, pausar, pedir_int
from ui.tables import tabla_cursos
from controllers.config_controller import (
    listar_config, actualizar_config,
    listar_modalidades as cfg_listar_modalidades, agregar_modalidad, actualizar_modalidad,
    listar_roles, agregar_rol,
    obtener_condiciones_curso, actualizar_condiciones_curso,
)
from controllers.curso_controller import listar_cursos, obtener_curso


class MenuConfiguracion:

    def mostrar(self):
        while True:
            limpiar()
            encabezado("CONFIGURACIÓN DEL SISTEMA", "Parámetros parametrizables")
            op = mostrar_menu("Configuración", [
                "Ver parámetros del sistema", "Editar parámetro",
                "Gestionar modalidades de cursado", "Gestionar roles de usuario",
                "Condiciones de inscripción por curso", "Volver",
            ])
            if op == "1":
                self._ver()
            elif op == "2":
                self._editar()
            elif op == "3":
                self._modalidades()
            elif op == "4":
                self._roles()
            elif op == "5":
                self._condiciones()
            elif op == "6":
                break
            else:
                err("Opción inválida.")
            pausar()

    def _ver(self):
        configs = listar_config()
        t = Table(box=box.ROUNDED, border_style="cyan", header_style="bold cyan",
                  title="[bold]Parámetros del Sistema[/]")
        t.add_column("Parámetro (clave)", min_width=30)
        t.add_column("Valor", min_width=20)
        t.add_column("Descripción")
        for c in configs:
            t.add_row(c["clave"], f"[cyan]{c['valor']}[/]", c["descripcion"] or "")
        console.print(t)

    def _editar(self):
        self._ver()
        clave = Prompt.ask("[white]  Clave a editar[/]").strip()
        if not clave:
            return
        nuevo_valor = Prompt.ask("[white]  Nuevo valor[/]").strip()
        if actualizar_config(clave, nuevo_valor):
            ok(f"Parámetro '{clave}' actualizado a '{nuevo_valor}'.")
        else:
            err("Clave no encontrada.")

    def _modalidades(self):
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

    def _roles(self):
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

    def _condiciones(self):
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
            title=f"[bold cyan]{curso['nombre']}[/]", border_style="cyan", box=box.ROUNDED,
        ))
        nuevas = Prompt.ask("[white]  Nuevas condiciones (Enter = sin cambios)[/]", default="").strip()
        if nuevas:
            actualizar_condiciones_curso(cid, nuevas)
            ok("Condiciones actualizadas.")
