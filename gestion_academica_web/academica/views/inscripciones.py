from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..decorators import rol_required, login_required, get_usuario_sesion
from ..models import Inscripcion, Estudiante, Cohorte


@rol_required('admin')
def lista(request):
    cohorte_id = request.GET.get('cohorte')
    estudiante_id = request.GET.get('estudiante')
    qs = Inscripcion.objects.select_related(
        'estudiante__usuario', 'cohorte__curso'
    ).order_by('-fecha_inscripcion')
    if cohorte_id:
        qs = qs.filter(cohorte_id=cohorte_id)
    if estudiante_id:
        qs = qs.filter(estudiante_id=estudiante_id)

    cohortes = Cohorte.objects.select_related('curso').order_by('-fecha_inicio')
    return render(request, 'inscripciones/list.html', {
        'inscripciones': qs,
        'cohortes': cohortes,
        'filtro_cohorte': cohorte_id,
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
def nueva(request):
    """Inscribir un estudiante en una cohorte (admin)."""
    cohorte_id = request.GET.get('cohorte') or request.POST.get('cohorte_id')
    estudiante_id = request.POST.get('estudiante_id')

    cohortes = Cohorte.objects.filter(activo=1).select_related('curso').order_by('nombre')
    estudiantes = Estudiante.objects.select_related('usuario').filter(
        usuario__activo=1
    ).order_by('usuario__apellido')

    if request.method == 'POST' and cohorte_id and estudiante_id:
        cohorte = get_object_or_404(Cohorte, pk=cohorte_id)
        estudiante = get_object_or_404(Estudiante, pk=estudiante_id)

        if not cohorte.cupo_disponible:
            messages.error(request, 'La cohorte no tiene cupo disponible.')
        elif Inscripcion.objects.filter(estudiante=estudiante, cohorte=cohorte).exists():
            messages.error(request, 'El estudiante ya está inscripto en esta cohorte.')
        else:
            from django.utils import timezone
            import datetime
            Inscripcion.objects.create(
                estudiante=estudiante, cohorte=cohorte,
                fecha_inscripcion=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                estado='activa',
            )
            messages.success(request, f'{estudiante} inscripto en {cohorte}.')
            return redirect('inscripciones_lista')

    cohorte_sel = None
    if cohorte_id:
        try:
            cohorte_sel = Cohorte.objects.select_related('curso').get(pk=cohorte_id)
        except Cohorte.DoesNotExist:
            pass

    return render(request, 'inscripciones/form.html', {
        'cohortes': cohortes,
        'estudiantes': estudiantes,
        'cohorte_sel': cohorte_sel,
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
def cancelar(request, pk):
    insc = get_object_or_404(Inscripcion, pk=pk)
    if request.method == 'POST':
        if insc.estado == 'activa':
            insc.estado = 'cancelada'
            insc.save()
            messages.success(request, 'Inscripción cancelada.')
        else:
            messages.warning(request, 'La inscripción ya no está activa.')
    return redirect('inscripciones_lista')


@rol_required('admin')
def reactivar(request, pk):
    insc = get_object_or_404(Inscripcion.objects.select_related('cohorte'), pk=pk)
    if request.method == 'POST':
        if insc.estado != 'cancelada':
            messages.warning(request, 'La inscripción ya está activa.')
        elif not insc.cohorte.cupo_disponible:
            messages.error(request, 'La cohorte no tiene cupo disponible.')
        else:
            insc.estado = 'activa'
            insc.save()
            messages.success(request, 'Inscripción reactivada.')
    return redirect('inscripciones_lista')


@login_required
def inscribirse(request):
    """Portal estudiante: inscribirse en una cohorte."""
    usuario = get_usuario_sesion(request)
    if usuario['rol'] != 'estudiante':
        return redirect('dashboard')

    perfil_id = usuario['perfil_id']
    try:
        estudiante = Estudiante.objects.get(pk=perfil_id)
    except Estudiante.DoesNotExist:
        messages.error(request, 'Perfil de estudiante no encontrado.')
        return redirect('dashboard')

    cohortes = Cohorte.objects.filter(activo=1).select_related('curso__modalidad').order_by('nombre')

    if request.method == 'POST':
        cohorte_id = request.POST.get('cohorte_id')
        cohorte = get_object_or_404(Cohorte, pk=cohorte_id, activo=1)

        if not cohorte.cupo_disponible:
            messages.error(request, 'La cohorte no tiene cupo disponible.')
        elif Inscripcion.objects.filter(estudiante=estudiante, cohorte=cohorte).exists():
            messages.error(request, 'Ya estás inscripto/a en esta cohorte.')
        else:
            import datetime
            Inscripcion.objects.create(
                estudiante=estudiante, cohorte=cohorte,
                fecha_inscripcion=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                estado='activa',
            )
            messages.success(request, f'Te inscribiste en {cohorte}.')
            return redirect('dashboard')

    return render(request, 'inscripciones/inscribirse.html', {
        'cohortes': cohortes,
        'usuario': usuario,
    })