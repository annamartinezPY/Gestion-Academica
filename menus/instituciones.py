from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from ui.helpers import console, limpiar, encabezado, ok, err, info, warn, mostrar_menu, pausar, pedir_int, pedir_email, pedir_telefono
from ui.tables import tabla_cursos
from controllers.institucion_controller import (
    listar_instituciones, obtener_institucion,
    registrar_institucion, actualizar_institucion, desactivar_institucion,
    listar_modalidades_institucion, agregar_modalidad_institucion, quitar_modalidad_institucion,
    listar_cursos_institucion, asignar_institucion_curso,
)
from controllers.config_controller import listar_modalidades as cfg_listar_modalidades
from controllers.curso_controller import listar_cursos


class MenuInstituciones:

    def mostrar(self):
        while True:
            limpiar()
            encabezado("GESTIÓN DE INSTITUCIONES")
            op = mostrar_menu("Instituciones", [
                "Listar instituciones", "Registrar nueva institución",
                "Ver detalle / editar institución", "Gestionar modalidades de institución",
                "Asignar cursos a institución", "Desactivar institución", "Volver",
            ])
            if op == "1":
                self._listar()
            elif op == "2":
                self._registrar()
            elif op == "3":
                self._editar()
            elif op == "4":
                self._gestionar_modalidades()
            elif op == "5":
                self._asignar_cursos()
            elif op == "6":
                self._desactivar()
            elif op == "7":
                break
            else:
                err("Opción inválida.")
                pausar()

    def _listar(self):
        limpiar()
        encabezado("LISTADO DE INSTITUCIONES")
        instituciones = listar_instituciones()
        if not instituciones:
            info("No hay instituciones registradas.")
            pausar()
            return
        tabla = Table(show_header=True, header_style="bold cyan", box=None)
        tabla.add_column("ID", style="dim", width=5)
        tabla.add_column("Nombre", style="bold")
        tabla.add_column("Email")
        tabla.add_column("Teléfono")
        tabla.add_column("Modalidades")
        tabla.add_column("Estado", justify="center")
        for i in instituciones:
            estado = "[green]Activa[/]" if i["activo"] else "[red]Inactiva[/]"
            tabla.add_row(str(i["id"]), i["nombre"],
                          i["email"] or "—", i["telefono"] or "—",
                          i["modalidades"] or "—", estado)
        console.print(tabla)
        pausar()

    def _registrar(self):
        limpiar()
        encabezado("NUEVA INSTITUCIÓN")
        nombre = Prompt.ask("Nombre de la institución").strip()
        if not nombre:
            err("El nombre es obligatorio.")
            pausar()
            return
        email = pedir_email("Email de contacto [opcional]", requerido=False)
        telefono = pedir_telefono("Teléfono de contacto [opcional]")
        inst_id = registrar_institucion(nombre, email, telefono)
        ok(f"Institución '{nombre}' registrada con ID {inst_id}.")
        pausar()

    def _editar(self):
        limpiar()
        encabezado("EDITAR INSTITUCIÓN")
        instituciones = listar_instituciones()
        if not instituciones:
            info("No hay instituciones registradas.")
            pausar()
            return
        for i in instituciones:
            console.print(f"  [dim]{i['id']}[/] — {i['nombre']}")
        inst_id = Prompt.ask("ID de la institución a editar").strip()
        inst = obtener_institucion(inst_id)
        if not inst:
            err("Institución no encontrada.")
            pausar()
            return
        nombre = Prompt.ask("Nombre", default=inst["nombre"]).strip()
        email = pedir_email("Email", requerido=False, default=inst["email"] or "")
        telefono = pedir_telefono("Teléfono", default=inst["telefono"] or "")
        actualizar_institucion(inst_id, nombre, email, telefono)
        ok("Institución actualizada.")
        pausar()

    def _gestionar_modalidades(self):
        limpiar()
        encabezado("MODALIDADES DE INSTITUCIÓN")
        instituciones = listar_instituciones(solo_activas=True)
        if not instituciones:
            info("No hay instituciones activas.")
            pausar()
            return
        for i in instituciones:
            console.print(f"  [dim]{i['id']}[/] — {i['nombre']}")
        inst_id = Prompt.ask("ID de la institución").strip()
        inst = obtener_institucion(inst_id)
        if not inst:
            err("Institución no encontrada.")
            pausar()
            return
        modalidades_asignadas = listar_modalidades_institucion(inst_id)
        asignadas_ids = {m["id"] for m in modalidades_asignadas}
        todas = cfg_listar_modalidades()
        console.print(f"\nModalidades de [bold]{inst['nombre']}[/]:")
        for m in todas:
            marca = "[green]✓[/]" if m["id"] in asignadas_ids else "  "
            console.print(f"  {marca} [{m['id']}] {m['nombre']}")
        accion = Prompt.ask("\n¿Qué desea hacer? [agregar/quitar]").strip().lower()
        if accion not in ("agregar", "quitar"):
            err("Acción inválida.")
            pausar()
            return
        mod_id = Prompt.ask("ID de la modalidad").strip()
        if accion == "agregar":
            exito, msg = agregar_modalidad_institucion(inst_id, mod_id)
        else:
            quitar_modalidad_institucion(inst_id, mod_id)
            exito, msg = True, "Modalidad quitada."
        ok(msg) if exito else err(msg)
        pausar()

    def _asignar_cursos(self):
        limpiar()
        encabezado("ASIGNAR CURSOS A INSTITUCIÓN")
        instituciones = listar_instituciones(solo_activas=True)
        if not instituciones:
            info("No hay instituciones activas.")
            pausar()
            return
        for i in instituciones:
            console.print(f"  [dim]{i['id']}[/] — {i['nombre']}")
        inst_id = Prompt.ask("ID de la institución").strip()
        inst = obtener_institucion(inst_id)
        if not inst:
            err("Institución no encontrada.")
            pausar()
            return
        cursos = listar_cursos()
        if not cursos:
            info("No hay cursos registrados.")
            pausar()
            return
        console.print("\nCursos disponibles:")
        for c in cursos:
            marca = "[green]✓[/]" if c["institucion_id"] == int(inst_id) else "  "
            console.print(f"  {marca} [{c['id']}] {c['nombre']}")
        curso_id = Prompt.ask("ID del curso a asignar").strip()
        asignar_institucion_curso(curso_id, inst_id)
        ok("Curso asignado a la institución.")
        pausar()

    def _desactivar(self):
        limpiar()
        encabezado("DESACTIVAR INSTITUCIÓN")
        instituciones = listar_instituciones(solo_activas=True)
        if not instituciones:
            info("No hay instituciones activas.")
            pausar()
            return
        for i in instituciones:
            console.print(f"  [dim]{i['id']}[/] — {i['nombre']}")
        inst_id = Prompt.ask("ID de la institución a desactivar").strip()
        inst = obtener_institucion(inst_id)
        if not inst:
            err("Institución no encontrada.")
            pausar()
            return
        if Confirm.ask(f"¿Desactivar '{inst['nombre']}'?"):
            desactivar_institucion(inst_id)
            ok("Institución desactivada.")
        pausar()
