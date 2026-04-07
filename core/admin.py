from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Usuario, Estudiante, Docente, Curso, Cohorte,
    Inscripcion, PagoEstudiante, PagoDocente, Sesion, Asistencia
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'rol', 'is_active']
    list_filter = ['rol', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informacion Adicional', {'fields': ('rol', 'telefono', 'direccion')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informacion Adicional', {'fields': ('rol', 'telefono', 'direccion')}),
    )


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ['cedula', 'nombre', 'apellido', 'email', 'telefono', 'activo']
    list_filter = ['activo']
    search_fields = ['cedula', 'nombre', 'apellido', 'email']
    ordering = ['apellido', 'nombre']


@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = ['cedula', 'nombre', 'apellido', 'email', 'especialidad', 'tarifa_hora', 'activo']
    list_filter = ['activo', 'especialidad']
    search_fields = ['cedula', 'nombre', 'apellido', 'email']
    ordering = ['apellido', 'nombre']


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'modalidad', 'duracion_horas', 'costo', 'activo']
    list_filter = ['modalidad', 'activo']
    search_fields = ['codigo', 'nombre']
    ordering = ['nombre']


@admin.register(Cohorte)
class CohorteAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'curso', 'docente', 'fecha_inicio', 'fecha_fin', 'estado', 'cupo_maximo']
    list_filter = ['estado', 'curso']
    search_fields = ['codigo', 'curso__nombre', 'docente__nombre']
    ordering = ['-fecha_inicio']


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ['estudiante', 'cohorte', 'fecha_inscripcion', 'estado', 'monto_acordado']
    list_filter = ['estado', 'cohorte']
    search_fields = ['estudiante__nombre', 'estudiante__apellido', 'cohorte__codigo']
    ordering = ['-fecha_inscripcion']


@admin.register(PagoEstudiante)
class PagoEstudianteAdmin(admin.ModelAdmin):
    list_display = ['inscripcion', 'monto', 'fecha_pago', 'metodo_pago', 'estado']
    list_filter = ['estado', 'metodo_pago']
    search_fields = ['inscripcion__estudiante__nombre', 'numero_recibo']
    ordering = ['-fecha_pago']


@admin.register(PagoDocente)
class PagoDocenteAdmin(admin.ModelAdmin):
    list_display = ['docente', 'cohorte', 'monto', 'horas_trabajadas', 'fecha_pago', 'estado']
    list_filter = ['estado', 'metodo_pago']
    search_fields = ['docente__nombre', 'numero_comprobante']
    ordering = ['-fecha_pago']


@admin.register(Sesion)
class SesionAdmin(admin.ModelAdmin):
    list_display = ['cohorte', 'numero_sesion', 'fecha', 'hora_inicio', 'hora_fin', 'tema']
    list_filter = ['cohorte']
    search_fields = ['cohorte__codigo', 'tema']
    ordering = ['cohorte', 'numero_sesion']


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ['sesion', 'estudiante', 'estado']
    list_filter = ['estado', 'sesion__cohorte']
    search_fields = ['estudiante__nombre', 'estudiante__apellido']
    ordering = ['sesion', 'estudiante__apellido']
