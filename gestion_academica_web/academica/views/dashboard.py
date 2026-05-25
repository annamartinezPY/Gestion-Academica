from datetime import date, timedelta
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.db.models import Count, Sum, Q
from ..decorators import login_required, get_usuario_sesion
from ..models import (
    Curso, Cohorte, Docente, Estudiante,
    Inscripcion, PagoDocente, PagoEstudiante, Notificacion, Sesion,
)


@login_required
def dashboard(request):
    usuario = get_usuario_sesion(request)
    rol = usuario['rol']
    ctx = {'usuario': usuario}

    if rol == 'admin':
        ctx.update({
            'total_cursos': Curso.objects.filter(activo=1).count(),
            'total_cohortes': Cohorte.objects.filter(activo=1).count(),
            'total_docentes': Docente.objects.select_related('usuario').filter(usuario__activo=1).count(),
            'total_estudiantes': Estudiante.objects.select_related('usuario').filter(usuario__activo=1).count(),
            'total_inscripciones': Inscripcion.objects.filter(estado='activa').count(),
            'pagos_pendientes': PagoDocente.objects.filter(estado='pendiente').count(),
            'cohortes_activas': Cohorte.objects.filter(activo=1).select_related('curso')[:5],
        })
        return render(request, 'dashboard_admin.html', ctx)

    elif rol == 'docente':
        perfil_id = usuario['perfil_id']
        if not perfil_id:
            return render(request, 'dashboard_docente.html', ctx)
        try:
            docente = Docente.objects.select_related('usuario').get(id=perfil_id)

            # Últimas 6 sesiones dictadas
            sesiones = (docente.sesiones
                        .select_related('cohorte__curso')
                        .order_by('-fecha', '-hora_inicio')[:6])

            # Top 5 cohortes con más estudiantes donde el docente dictó clases
            top_cohortes = (Cohorte.objects
                            .filter(sesiones__docente=docente)
                            .annotate(
                                total_estudiantes=Count(
                                    'inscripciones',
                                    filter=Q(inscripciones__estado='activa')
                                ),
                                total_sesiones=Count('sesiones',
                                                     filter=Q(sesiones__docente=docente))
                            )
                            .select_related('curso')
                            .order_by('-total_estudiantes')
                            .distinct()[:5])

            # Resumen salarial
            total_cobrado = (docente.pagos
                             .filter(estado='pagado')
                             .aggregate(t=Sum('monto'))['t'] or 0)
            total_pendiente = (docente.pagos
                               .filter(estado='pendiente')
                               .aggregate(t=Sum('monto'))['t'] or 0)
            total_sesiones = docente.sesiones.count()

            ctx.update({
                'docente': docente,
                'sesiones': sesiones,
                'top_cohortes': top_cohortes,
                'total_cobrado': total_cobrado,
                'total_pendiente': total_pendiente,
                'total_sesiones': total_sesiones,
            })
        except Docente.DoesNotExist:
            pass
        return render(request, 'dashboard_docente.html', ctx)

    elif rol == 'estudiante':
        perfil_id = usuario['perfil_id']
        if not perfil_id:
            return render(request, 'dashboard_estudiante.html', ctx)
        try:
            estudiante = Estudiante.objects.select_related('usuario').get(id=perfil_id)
            inscripciones = estudiante.inscripciones.select_related(
                'cohorte__curso'
            ).filter(estado='activa')

            # Pagos pendientes con vencimiento próximo (próximos 5 días) o vencidos
            limite = (date.today() + timedelta(days=5)).isoformat()
            pagos_alertas = PagoEstudiante.objects.filter(
                inscripcion__estudiante=estudiante,
                estado='pendiente',
                fecha_vencimiento__isnull=False,
                fecha_vencimiento__lte=limite,
            ).select_related('inscripcion__cohorte__curso').order_by('fecha_vencimiento')

            # Notificaciones no leídas
            notificaciones = Notificacion.objects.filter(
                usuario=estudiante.usuario, leida=0
            ).order_by('-fecha')[:5]

            ctx.update({
                'estudiante': estudiante,
                'inscripciones': inscripciones,
                'pagos_alertas': pagos_alertas,
                'notificaciones': notificaciones,
            })
        except Estudiante.DoesNotExist:
            pass
        return render(request, 'dashboard_estudiante.html', ctx)

    return redirect('login')