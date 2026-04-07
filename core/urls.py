"""
URL patterns for core app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Autenticacion
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),
    
    # Estudiantes
    path('estudiantes/', views.estudiante_list, name='estudiante_list'),
    path('estudiantes/crear/', views.estudiante_create, name='estudiante_create'),
    path('estudiantes/<int:pk>/', views.estudiante_detail, name='estudiante_detail'),
    path('estudiantes/<int:pk>/editar/', views.estudiante_update, name='estudiante_update'),
    path('estudiantes/<int:pk>/eliminar/', views.estudiante_delete, name='estudiante_delete'),
    
    # Docentes
    path('docentes/', views.docente_list, name='docente_list'),
    path('docentes/crear/', views.docente_create, name='docente_create'),
    path('docentes/<int:pk>/', views.docente_detail, name='docente_detail'),
    path('docentes/<int:pk>/editar/', views.docente_update, name='docente_update'),
    path('docentes/<int:pk>/eliminar/', views.docente_delete, name='docente_delete'),
    
    # Cursos
    path('cursos/', views.curso_list, name='curso_list'),
    path('cursos/crear/', views.curso_create, name='curso_create'),
    path('cursos/<int:pk>/', views.curso_detail, name='curso_detail'),
    path('cursos/<int:pk>/editar/', views.curso_update, name='curso_update'),
    path('cursos/<int:pk>/eliminar/', views.curso_delete, name='curso_delete'),
    
    # Cohortes
    path('cohortes/', views.cohorte_list, name='cohorte_list'),
    path('cohortes/crear/', views.cohorte_create, name='cohorte_create'),
    path('cohortes/<int:pk>/', views.cohorte_detail, name='cohorte_detail'),
    path('cohortes/<int:pk>/editar/', views.cohorte_update, name='cohorte_update'),
    path('cohortes/<int:pk>/eliminar/', views.cohorte_delete, name='cohorte_delete'),
    
    # Inscripciones
    path('inscripciones/', views.inscripcion_list, name='inscripcion_list'),
    path('inscripciones/crear/', views.inscripcion_create, name='inscripcion_create'),
    path('inscripciones/<int:pk>/', views.inscripcion_detail, name='inscripcion_detail'),
    path('inscripciones/<int:pk>/editar/', views.inscripcion_update, name='inscripcion_update'),
    path('inscripciones/<int:pk>/cancelar/', views.inscripcion_cancelar, name='inscripcion_cancelar'),
    
    # Pagos Estudiantes
    path('pagos/', views.pago_estudiante_list, name='pago_estudiante_list'),
    path('pagos/crear/', views.pago_estudiante_create, name='pago_estudiante_create'),
    path('pagos/<int:pk>/', views.pago_estudiante_detail, name='pago_estudiante_detail'),
    path('pagos/<int:pk>/verificar/', views.pago_estudiante_verificar, name='pago_estudiante_verificar'),
    
    # Pagos Docentes
    path('pagos-docentes/', views.pago_docente_list, name='pago_docente_list'),
    path('pagos-docentes/crear/', views.pago_docente_create, name='pago_docente_create'),
    path('pagos-docentes/<int:pk>/', views.pago_docente_detail, name='pago_docente_detail'),
    
    # Sesiones y Asistencia
    path('cohortes/<int:cohorte_pk>/sesiones/', views.sesion_list, name='sesion_list'),
    path('cohortes/<int:cohorte_pk>/sesiones/crear/', views.sesion_create, name='sesion_create'),
    path('sesiones/<int:pk>/asistencia/', views.asistencia_registrar, name='asistencia_registrar'),
    
    # Reportes
    path('reportes/', views.reportes_dashboard, name='reportes_dashboard'),
    path('reportes/ingresos/', views.reporte_ingresos, name='reporte_ingresos'),
    path('reportes/pagos-docentes/', views.reporte_pagos_docentes, name='reporte_pagos_docentes'),
    path('reportes/asistencia/', views.reporte_asistencia, name='reporte_asistencia'),
    
    # API para AJAX
    path('api/asistencia/guardar/', views.api_guardar_asistencia, name='api_guardar_asistencia'),
]
