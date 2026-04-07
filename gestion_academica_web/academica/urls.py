from django.urls import path
from .views import auth, dashboard, docentes, estudiantes, cursos, cohortes, inscripciones, pagos, reportes

urlpatterns = [
    # Auth
    path('login/', auth.login_view, name='login'),
    path('logout/', auth.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', dashboard.dashboard, name='dashboard'),

    # Docentes
    path('docentes/', docentes.lista, name='docentes_lista'),
    path('docentes/nuevo/', docentes.nuevo, name='docentes_nuevo'),
    path('docentes/<int:pk>/', docentes.detalle, name='docentes_detalle'),
    path('docentes/<int:pk>/editar/', docentes.editar, name='docentes_editar'),
    path('docentes/<int:pk>/desactivar/', docentes.desactivar, name='docentes_desactivar'),

    # Estudiantes
    path('estudiantes/', estudiantes.lista, name='estudiantes_lista'),
    path('estudiantes/nuevo/', estudiantes.nuevo, name='estudiantes_nuevo'),
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
    path('cohortes/<int:pk>/sesiones/nueva/', cohortes.nueva_sesion, name='cohortes_nueva_sesion'),
    path('cohortes/<int:pk>/sesiones/<int:sesion_pk>/eliminar/', cohortes.eliminar_sesion, name='cohortes_eliminar_sesion'),

    # Inscripciones
    path('inscripciones/', inscripciones.lista, name='inscripciones_lista'),
    path('inscripciones/nueva/', inscripciones.nueva, name='inscripciones_nueva'),
    path('inscripciones/<int:pk>/cancelar/', inscripciones.cancelar, name='inscripciones_cancelar'),
    path('inscripciones/<int:pk>/reactivar/', inscripciones.reactivar, name='inscripciones_reactivar'),
    path('inscripciones/inscribirse/', inscripciones.inscribirse, name='inscribirse'),

    # Pagos
    path('pagos/estudiantes/', pagos.lista_estudiantes, name='pagos_estudiantes'),
    path('pagos/estudiantes/nuevo/', pagos.nuevo_pago_estudiante, name='pagos_estudiantes_nuevo'),
    path('pagos/estudiantes/<int:pk>/anular/', pagos.anular_pago_estudiante, name='pagos_estudiantes_anular'),
    path('pagos/docentes/', pagos.lista_docentes, name='pagos_docentes'),
    path('pagos/docentes/nuevo/', pagos.nuevo_pago_docente, name='pagos_docentes_nuevo'),
    path('pagos/docentes/<int:pk>/pagado/', pagos.marcar_pagado_docente, name='pagos_docentes_pagado'),
    path('pagos/docentes/<int:pk>/anular/', pagos.anular_pago_docente, name='pagos_docentes_anular'),

    # Reportes
    path('reportes/', reportes.index, name='reportes'),
]