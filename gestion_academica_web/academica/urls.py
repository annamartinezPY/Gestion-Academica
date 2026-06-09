from django.urls import path
from .views import auth, dashboard, docentes, estudiantes, cursos, cohortes, inscripciones, pagos, reportes, instituciones, catalogo, mis_pagos, mi_salario, permisos, password_reset, config_curso, niveles_educativos, tipos_contratacion, asistencia, materiales, tareas, notificaciones, usuarios

urlpatterns = [
    # Auth
    path('login/', auth.login_view, name='login'),
    path('logout/', auth.logout_view, name='logout'),
    path('recuperar-contrasena/', password_reset.solicitar_reset, name='password_reset_solicitar'),
    path('reset-password/<str:token>/', password_reset.nueva_contrasena, name='password_reset_nueva'),
    path('cambio-password-forzado/', auth.cambio_password_forzado, name='password_cambio_forzado'),

    # Dashboard
    path('dashboard/', dashboard.dashboard, name='dashboard'),

    # Instituciones
    path('instituciones/', instituciones.InstitucionListView.as_view(), name='instituciones_lista'),
    path('instituciones/nueva/', instituciones.InstitucionCreateView.as_view(), name='instituciones_nueva'),
    path('instituciones/<int:pk>/', instituciones.InstitucionDetailView.as_view(), name='instituciones_detalle'),
    path('instituciones/<int:pk>/desactivar/', instituciones.InstitucionDeactivateView.as_view(), name='instituciones_desactivar'),
    path('instituciones/<int:pk>/asignar-curso/', instituciones.InstitucionAsignarCursoView.as_view(), name='instituciones_asignar_curso'),
    path('instituciones/<int:pk>/cursos/<int:curso_pk>/desasignar/', instituciones.InstitucionDesasignarCursoView.as_view(), name='instituciones_desasignar_curso'),
    path('instituciones/<int:pk>/cursos/nuevo/', instituciones.InstitucionCrearCursoView.as_view(), name='instituciones_crear_curso'),
    path('instituciones/<int:pk>/docentes/', instituciones.InstitucionDocenteView.as_view(), name='instituciones_docentes'),
    path('instituciones/<int:pk>/modalidades/', instituciones.InstitucionModalidadView.as_view(), name='instituciones_modalidades'),

    # Docentes
    path('docentes/', docentes.lista, name='docentes_lista'),
    path('docentes/<int:pk>/', docentes.detalle, name='docentes_detalle'),
    path('docentes/<int:pk>/perfil/', docentes.perfil_completo, name='docentes_perfil_completo'),
    path('docentes/<int:pk>/editar/', docentes.editar, name='docentes_editar'),
    path('docentes/<int:pk>/desactivar/', docentes.desactivar, name='docentes_desactivar'),
    path('docentes/<int:pk>/activar/', docentes.activar, name='docentes_activar'),
    path('docentes/<int:pk>/reset-password/', docentes.reset_password, name='docentes_reset_password'),
    path('docentes/<int:pk>/instituciones/vincular/', docentes.institucion_vincular, name='docentes_institucion_vincular'),
    path('docentes/<int:pk>/instituciones/<int:vinc_pk>/actualizar/', docentes.institucion_actualizar, name='docentes_institucion_actualizar'),
    path('docentes/<int:pk>/instituciones/<int:vinc_pk>/desvincular/', docentes.institucion_desvincular, name='docentes_institucion_desvincular'),

    # Niveles educativos (submenu de Docentes)
    path('docentes/niveles-educativos/', niveles_educativos.lista, name='niveles_educativos_lista'),
    path('docentes/niveles-educativos/nuevo/', niveles_educativos.nuevo, name='niveles_educativos_nuevo'),
    path('docentes/niveles-educativos/<int:pk>/editar/', niveles_educativos.editar, name='niveles_educativos_editar'),
    path('docentes/niveles-educativos/<int:pk>/eliminar/', niveles_educativos.eliminar, name='niveles_educativos_eliminar'),

    # Tipos de contratacion (submenu de Docentes)
    path('docentes/tipos-contratacion/', tipos_contratacion.lista, name='tipos_contratacion_lista'),
    path('docentes/tipos-contratacion/nuevo/', tipos_contratacion.nuevo, name='tipos_contratacion_nuevo'),
    path('docentes/tipos-contratacion/<int:pk>/editar/', tipos_contratacion.editar, name='tipos_contratacion_editar'),
    path('docentes/tipos-contratacion/<int:pk>/eliminar/', tipos_contratacion.eliminar, name='tipos_contratacion_eliminar'),

    # Estudiantes
    path('estudiantes/', estudiantes.lista, name='estudiantes_lista'),
    path('estudiantes/<int:pk>/', estudiantes.detalle, name='estudiantes_detalle'),
    path('estudiantes/<int:pk>/editar/', estudiantes.editar, name='estudiantes_editar'),

    # Cursos
    path('cursos/', cursos.lista, name='cursos_lista'),
    path('cursos/nuevo/', cursos.nuevo, name='cursos_nuevo'),
    path('cursos/<int:pk>/editar/', cursos.editar, name='cursos_editar'),
    path('cursos/<int:pk>/desactivar/', cursos.desactivar, name='cursos_desactivar'),

    # Cohortes
    path('cohortes/', cohortes.lista, name='cohortes_lista'),
    path('cohortes/nueva/', cohortes.nueva, name='cohortes_nueva'),
    path('cohortes/<int:pk>/', cohortes.detalle, name='cohortes_detalle'),
    path('cohortes/<int:pk>/editar/', cohortes.editar, name='cohortes_editar'),
    path('cohortes/<int:pk>/desactivar/', cohortes.desactivar, name='cohortes_desactivar'),
    path('cohortes/<int:pk>/activar/', cohortes.activar, name='cohortes_activar'),
    path('cohortes/<int:pk>/sesiones/nueva/', cohortes.nueva_sesion, name='cohortes_nueva_sesion'),
    path('cohortes/<int:pk>/sesiones/<int:sesion_pk>/eliminar/', cohortes.eliminar_sesion, name='cohortes_eliminar_sesion'),
    path('cohortes/<int:pk>/sesiones/calendario.json', cohortes.sesiones_calendario_json, name='cohortes_sesiones_calendario_json'),

    # Asistencia
    path('cohortes/<int:pk>/sesiones/<int:sesion_pk>/iniciar/', asistencia.iniciar_sesion, name='asistencia_iniciar'),
    path('cohortes/<int:pk>/sesiones/<int:sesion_pk>/finalizar/', asistencia.finalizar_sesion, name='asistencia_finalizar'),
    path('cohortes/<int:pk>/sesiones/<int:sesion_pk>/asistencia/', asistencia.marcar, name='asistencia_marcar'),

    # Materiales del curso
    path('cohortes/<int:cohorte_id>/materiales/', materiales.lista_por_cohorte, name='materiales_cohorte'),
    path('cohortes/<int:cohorte_id>/materiales/nuevo/', materiales.nuevo, name='materiales_nuevo'),
    path('cohortes/<int:cohorte_id>/materiales/<int:pk>/eliminar/', materiales.eliminar, name='materiales_eliminar'),

    # Tareas
    path('cohortes/<int:cohorte_id>/tareas/', tareas.lista_por_cohorte, name='tareas_cohorte'),
    path('cohortes/<int:cohorte_id>/tareas/nueva/', tareas.nueva, name='tareas_nueva'),
    path('cohortes/<int:cohorte_id>/tareas/<int:pk>/eliminar/', tareas.eliminar, name='tareas_eliminar'),
    path('cohortes/<int:cohorte_id>/tareas/<int:pk>/entregar/', tareas.entregar, name='tareas_entregar'),
    path('cohortes/<int:cohorte_id>/tareas/<int:pk>/entregas/', tareas.ver_entregas, name='tareas_entregas'),

    # Inscripciones
    path('inscripciones/', inscripciones.lista, name='inscripciones_lista'),
    path('inscripciones/nueva/', inscripciones.nueva, name='inscripciones_nueva'),
    path('inscripciones/<int:pk>/cancelar/', inscripciones.cancelar, name='inscripciones_cancelar'),
    path('inscripciones/<int:pk>/reactivar/', inscripciones.reactivar, name='inscripciones_reactivar'),
    path('inscripciones/inscribirse/', inscripciones.inscribirse, name='inscribirse'),

    # Pagos
    path('pagos/estudiantes/', pagos.lista_estudiantes, name='pagos_estudiantes'),
    path('pagos/estudiantes/nuevo/', pagos.nuevo_pago_estudiante, name='pagos_nuevo_estudiante'),
    path('pagos/estudiantes/<int:pk>/anular/', pagos.anular_pago_estudiante, name='pagos_anular_estudiante'),
    path('pagos/estudiantes/<int:pk>/revision/', pagos.poner_en_revision, name='pagos_en_revision'),
    path('pagos/estudiantes/<int:pk>/aprobar/', pagos.aprobar_pago, name='pagos_aprobar'),
    path('pagos/estudiantes/<int:pk>/rechazar/', pagos.rechazar_pago, name='pagos_rechazar'),
    path('pagos/docentes/', pagos.lista_docentes, name='pagos_docentes'),
    path('pagos/docentes/nuevo/', pagos.nuevo_pago_docente, name='pagos_nuevo_docente'),
    path('pagos/docentes/<int:pk>/pagado/', pagos.marcar_pagado_docente, name='pagos_marcar_pagado_docente'),
    path('pagos/docentes/<int:pk>/anular/', pagos.anular_pago_docente, name='pagos_anular_docente'),

    # Reportes
    path('reportes/', reportes.index, name='reportes'),

    # Notificaciones
    path('notificaciones/', notificaciones.lista, name='notificaciones_lista'),
    path('notificaciones/<int:pk>/abrir/', notificaciones.abrir, name='notificaciones_abrir'),
    path('notificaciones/<int:pk>/leer/', notificaciones.marcar_leida, name='notificaciones_leer'),
    path('notificaciones/leer-todas/', notificaciones.marcar_todas, name='notificaciones_leer_todas'),

    # Catálogo de capacitaciones
    path('catalogo/', catalogo.catalogo, name='catalogo'),
    path('catalogo/cohorte/<int:pk>/', catalogo.cohorte_detalle, name='catalogo_cohorte_detalle'),

    # Portal estudiante — mis pagos
    path('mis-pagos/', mis_pagos.mis_pagos, name='mis_pagos'),
    path('mis-pagos/registrar/', mis_pagos.registrar_pago, name='mis_pagos_registrar'),

    # Portal docente — mi salario
    path('mi-salario/', mi_salario.mi_salario, name='mi_salario'),

    # Banco central de usuarios
    path('usuarios/', usuarios.lista, name='usuarios_lista'),
    path('usuarios/nuevo/', usuarios.nuevo, name='usuarios_nuevo'),

    # Gestión de permisos por rol
    path('config/permisos/', permisos.lista_roles, name='permisos_roles'),
    path('config/permisos/<int:rol_id>/', permisos.gestionar_rol, name='permisos_gestionar'),
    path('config/permisos/<int:rol_id>/editar/', permisos.editar_rol, name='permisos_editar_rol'),
    path('config/permisos/<int:rol_id>/toggle/', permisos.toggle_activo, name='permisos_toggle_rol'),

    # Configuración de Curso (modalidades + condiciones)
    path('config/curso/', config_curso.index, name='config_curso'),
    path('config/curso/modalidades/nueva/', config_curso.nueva_modalidad, name='config_nueva_modalidad'),
    path('config/curso/modalidades/<int:pk>/editar/', config_curso.editar_modalidad, name='config_editar_modalidad'),
    path('config/curso/modalidades/<int:pk>/eliminar/', config_curso.eliminar_modalidad, name='config_eliminar_modalidad'),
    path('config/curso/condiciones/nueva/', config_curso.nueva_condicion, name='config_nueva_condicion'),
    path('config/curso/condiciones/<int:pk>/editar/', config_curso.editar_condicion, name='config_editar_condicion'),
    path('config/curso/condiciones/<int:pk>/eliminar/', config_curso.eliminar_condicion, name='config_eliminar_condicion'),
]