from ui.helpers import limpiar, encabezado, ok, err, mostrar_menu, pausar
from menus.usuarios import MenuUsuarios
from menus.estudiantes import MenuEstudiantes
from menus.docentes import MenuDocentes
from menus.instituciones import MenuInstituciones
from menus.cursos import MenuCursos
from menus.cohortes import MenuCohortes
from menus.inscripciones import MenuInscripciones
from menus.pagos import MenuPagos
from menus.asistencias import MenuAsistencias
from menus.reportes import MenuReportes
from menus.configuracion import MenuConfiguracion


class PortalAdmin:

    def __init__(self, usuario):
        self.usuario = usuario
        self.menus = {
            "1":  MenuUsuarios(),
            "2":  MenuEstudiantes(),
            "3":  MenuDocentes(),
            "4":  MenuInstituciones(),
            "5":  MenuCursos(),
            "6":  MenuCohortes(),
            "7":  MenuInscripciones(),
            "8":  MenuPagos(),
            "9":  MenuAsistencias(),
            "10": MenuReportes(),
            "11": MenuConfiguracion(),
        }

    def mostrar(self):
        while True:
            limpiar()
            encabezado("PANEL DE ADMINISTRADOR",
                       f"Usuario: {self.usuario['nombre']} {self.usuario['apellido']}")
            op = mostrar_menu("Menú Administrador", [
                "Gestión de usuarios",
                "Gestión de estudiantes",
                "Gestión de docentes",
                "Gestión de instituciones",
                "Gestión de cursos",
                "Gestión de cohortes",
                "Gestión de inscripciones",
                "Gestión de pagos",
                "Gestión de asistencias",
                "Reportes académicos y administrativos",
                "Configuración del sistema",
                "Cerrar sesión",
            ])
            if op in self.menus:
                self.menus[op].mostrar()
            elif op == "12":
                ok("Sesión cerrada.")
                pausar()
                break
            else:
                err("Opción inválida.")
                pausar()
