from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from ..decorators import permiso_required, login_required, get_usuario_sesion
from ..models import Inscripcion, Estudiante, Cohorte, Institucion, Docente


@permiso_required('inscripciones.ver')
def lista(request):
    usuario_sesion = get_usuario_sesion(request)

    cohorte_id    = request.GET.get('cohorte', '')
    estudiante_id = request.GET.get('estudiante', '')
    inst_id       = request.GET.get('institucion', '')
    anio          = request.GET.get('anio', '')
    estado        = request.GET.get('estado', '')

    qs = Inscripcion.objects.select_related(
        'estudiante__usuario',
        'cohorte__curso__institucion',
        'cohorte__curso__modalidad',
    ).order_by('-fecha_inscripcion')

    # Si el usuario es docente, sólo ve inscripciones a SUS cohortes
    # (donde es titular o dicta sesiones).
    cohortes_visibles = None
    mis_cohortes = None
    if usuario_sesion['rol'] == 'docente' and usuario_sesion.get('perfil_id'):
        try:
            docente = Docente.objects.get(pk=usuario_sesion['perfil_id'])
            cohortes_titular = Cohorte.objects.filter(docente=docente).values_list('id', flat=True)
            cohortes_sesiones = docente.sesiones.values_list('cohorte_id', flat=True)
            cohortes_visibles = set(cohortes_titular) | set(cohortes_sesiones)
            qs = qs.filter(cohorte_id__in=cohortes_visibles)

            # Cohortes del docente con totales para mostrar en la card de resumen
            mis_cohortes = (Cohorte.objects
                            .filter(id__in=cohortes_visibles)
                            .select_related('curso__modalidad', 'curso__institucion')
                            .annotate(
                                total_inscriptos=Count(
                                    'inscripciones',
                                    filter=Q(inscripciones__estado='activa')
                                ),
                            )
                            .order_by('-fecha_inicio'))
        except Docente.DoesNotExist:
            qs = qs.none()
            cohortes_visibles = set()
            mis_cohortes = Cohorte.objects.none()

    if cohorte_id:
        qs = qs.filter(cohorte_id=cohorte_id)
    if estudiante_id:
        qs = qs.filter(estudiante_id=estudiante_id)
    if inst_id:
        qs = qs.filter(cohorte__curso__institucion_id=inst_id)
    if anio:
        qs = qs.filter(cohorte__fecha_inicio__startswith=anio)
    if estado:
        qs = qs.filter(estado=estado)

    cohortes = Cohorte.objects.select_related('curso').order_by('-fecha_inicio')
    if cohortes_visibles is not None:
        cohortes = cohortes.filter(id__in=cohortes_visibles)
    instituciones = Institucion.objects.filter(activo=1).order_by('nombre')

    # Años disponibles (de las cohortes existentes)
    anios = sorted({
        f[:4]
        for f in Cohorte.objects.values_list('fecha_inicio', flat=True)
        if f and len(f) >= 4
    }, reverse=True)

    hay_filtros = any([cohorte_id, inst_id, anio, estado])

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    qs_parts = []
    if cohorte_id: qs_parts.append(f'cohorte={cohorte_id}')
    if estudiante_id: qs_parts.append(f'estudiante={estudiante_id}')
    if inst_id: qs_parts.append(f'institucion={inst_id}')
    if anio: qs_parts.append(f'anio={anio}')
    if estado: qs_parts.append(f'estado={estado}')

    return render(request, 'inscripciones/list.html', {
        'inscripciones': page_obj,
        'page_obj': page_obj,
        'querystring': '&'.join(qs_parts),
        'cohortes': cohortes,
        'instituciones': instituciones,
        'anios': anios,
        'filtro_cohorte': cohorte_id,
        'filtro_institucion': inst_id,
        'filtro_anio': anio,
        'filtro_estado': estado,
        'hay_filtros': hay_filtros,
        'mis_cohortes': mis_cohortes,
        'usuario': usuario_sesion,
    })


@permiso_required('inscripciones.crear')
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


@permiso_required('inscripciones.cancelar')
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


@permiso_required('inscripciones.cancelar')
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