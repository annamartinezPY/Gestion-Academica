from django.shortcuts import render, redirect
from ..decorators import login_required, get_usuario_sesion
from ..models import (
    Curso, Cohorte, Docente, Estudiante,
    Inscripcion, PagoDocente, PagoEstudiante,
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
            sesiones = docente.sesiones.select_related('cohorte__curso').order_by('-fecha')[:5]
            pagos = docente.pagos.order_by('-fecha_pago')[:5]
            ctx.update({'docente': docente, 'sesiones': sesiones, 'pagos': pagos})
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
            ctx.update({'estudiante': estudiante, 'inscripciones': inscripciones})
        except Estudiante.DoesNotExist:
            pass
        return render(request, 'dashboard_estudiante.html', ctx)

    return redirect('login')