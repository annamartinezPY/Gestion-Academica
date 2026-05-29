import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from ..decorators import permiso_required, get_usuario_sesion
from ..models import Cohorte, Sesion, Docente, Inscripcion, Curso, Institucion
from ..forms import CohorteForm, SesionForm


def _cursos_json():
    """Serializa cursos activos con su institucion_id para filtrado JS."""
    cursos = Curso.objects.filter(activo=1).select_related('institucion', 'modalidad')
    data = [
        {
            'id': c.id,
            'nombre': c.nombre,
            'modalidad': c.modalidad.nombre,
            'institucion_id': c.institucion_id or 0,
            'horas_totales': c.horas_totales or 0,
        }
        for c in cursos
    ]
    return json.dumps(data)


def _iso_a_ddmmaaaa(valor):
    """Convierte 'YYYY-MM-DD' -> 'DD/MM/YYYY' para mostrar en el form."""
    if not valor:
        return ''
    import re as _re
    m = _re.match(r'^(\d{4})-(\d{2})-(\d{2})$', str(valor).strip())
    if m:
        y, mo, d = m.groups()
        return f'{d}/{mo}/{y}'
    return str(valor)


@permiso_required('cohortes.ver')
def lista(request):
    qs = (Cohorte.objects
          .select_related('curso__modalidad', 'curso__institucion')
          .order_by('-fecha_inicio'))
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(nombre__icontains=q) | qs.filter(curso__nombre__icontains=q)
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'cohortes/list.html', {
        'cohortes': page_obj,
        'page_obj': page_obj,
        'q': q,
        'querystring': f'q={q}' if q else '',
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('cohortes.crear')
def nueva(request):
    form = CohorteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        docente_id = d.get('docente') or None
        Cohorte.objects.create(
            nombre=d['nombre'],
            curso=d['curso'],
            fecha_inicio=d['fecha_inicio'],
            fecha_fin=d['fecha_fin'],
            cupo_maximo=d['cupo_maximo'],
            dias_clase=','.join(d.get('dias_clase') or []),
            carga_horaria_diaria=d.get('carga_horaria_diaria') or 0,
            docente_id=docente_id,
            activo=1,
        )
        messages.success(request, f'Cohorte "{d["nombre"]}" creada.')
        return redirect('cohortes_lista')
    return render(request, 'cohortes/form.html', {
        'form': form,
        'titulo': 'Nueva Cohorte',
        'cursos_json': _cursos_json(),
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('cohortes.editar')
def editar(request, pk):
    cohorte = get_object_or_404(
        Cohorte.objects.select_related('curso__institucion'), pk=pk
    )
    initial = {
        'nombre': cohorte.nombre,
        'institucion': cohorte.curso.institucion if cohorte.curso.institucion_id else None,
        'curso': cohorte.curso,
        'fecha_inicio': _iso_a_ddmmaaaa(cohorte.fecha_inicio),
        'fecha_fin': _iso_a_ddmmaaaa(cohorte.fecha_fin),
        'cupo_maximo': cohorte.cupo_maximo,
        'dias_clase': cohorte.dias_lista,
        'carga_horaria_diaria': cohorte.carga_horaria_diaria or 0,
        'docente': cohorte.docente_id or '',
    }
    form = CohorteForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        cohorte.nombre = d['nombre']
        cohorte.curso = d['curso']
        cohorte.fecha_inicio = d['fecha_inicio']
        cohorte.fecha_fin = d['fecha_fin']
        cohorte.cupo_maximo = d['cupo_maximo']
        cohorte.dias_clase = ','.join(d.get('dias_clase') or [])
        cohorte.carga_horaria_diaria = d.get('carga_horaria_diaria') or 0
        cohorte.docente_id = d.get('docente') or None
        cohorte.save()
        messages.success(request, 'Cohorte actualizada.')
        return redirect('cohortes_lista')
    return render(request, 'cohortes/form.html', {
        'form': form,
        'titulo': 'Editar Cohorte',
        'cohorte': cohorte,
        'cursos_json': _cursos_json(),
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('cohortes.ver')
def detalle(request, pk):
    cohorte = get_object_or_404(Cohorte.objects.select_related('curso__modalidad'), pk=pk)
    sesiones = cohorte.sesiones.select_related('docente__usuario').order_by('fecha', 'hora_inicio')
    inscripciones = cohorte.inscripciones.select_related(
        'estudiante__usuario'
    ).order_by('estado', 'fecha_inscripcion')
    docentes = Docente.objects.select_related('usuario').filter(usuario__activo=1)
    form_sesion = SesionForm()
    return render(request, 'cohortes/detail.html', {
        'cohorte': cohorte, 'sesiones': sesiones,
        'inscripciones': inscripciones, 'docentes': docentes,
        'form_sesion': form_sesion,
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('cohortes.ver')
def sesiones_calendario_json(request, pk):
    """Devuelve las sesiones de la cohorte en formato FullCalendar."""
    cohorte = get_object_or_404(Cohorte, pk=pk)
    sesiones = (cohorte.sesiones
                .select_related('docente__usuario')
                .order_by('fecha', 'hora_inicio'))

    # Paleta por estado
    colors = {
        'planificada': '#572364',
        'en_curso':    '#f59e0b',
        'finalizada':  '#16a34a',
        'cancelada':   '#9ca3af',
    }

    events = []
    for s in sesiones:
        if not s.fecha or not s.hora_inicio or not s.hora_fin:
            continue
        fecha = str(s.fecha)[:10]
        hi = str(s.hora_inicio)[:5]
        hf = str(s.hora_fin)[:5]
        docente_nombre = ''
        if s.docente_id and s.docente.usuario:
            docente_nombre = f'{s.docente.usuario.apellido}, {s.docente.usuario.nombre}'
        title = s.tema or 'Sesión'
        estado = s.estado or 'planificada'
        events.append({
            'id': s.id,
            'title': title,
            'start': f'{fecha}T{hi}',
            'end':   f'{fecha}T{hf}',
            'color': colors.get(estado, '#572364'),
            'extendedProps': {
                'docente': docente_nombre,
                'estado': estado,
                'tema': s.tema or '',
            },
        })
    return JsonResponse(events, safe=False)


@permiso_required('cohortes.sesiones')
def nueva_sesion(request, pk):
    cohorte = get_object_or_404(Cohorte, pk=pk)
    form = SesionForm(request.POST)
    if form.is_valid():
        d = form.cleaned_data
        docente_id = request.POST.get('docente_id')
        if not docente_id:
            messages.error(request, 'Debe seleccionar un docente.')
            return redirect('cohortes_detalle', pk=pk)
        try:
            docente = Docente.objects.get(pk=docente_id)
        except Docente.DoesNotExist:
            messages.error(request, 'Docente no encontrado.')
            return redirect('cohortes_detalle', pk=pk)
        Sesion.objects.create(
            cohorte=cohorte, docente=docente,
            fecha=d['fecha'], hora_inicio=d['hora_inicio'],
            hora_fin=d['hora_fin'], tema=d.get('tema') or '',
        )
        messages.success(request, 'Sesión registrada.')
    else:
        for field, errs in form.errors.items():
            for e in errs:
                messages.error(request, f'{field}: {e}')
    return redirect('cohortes_detalle', pk=pk)


@permiso_required('cohortes.sesiones')
def eliminar_sesion(request, pk, sesion_pk):
    sesion = get_object_or_404(Sesion, pk=sesion_pk, cohorte_id=pk)
    if request.method == 'POST':
        sesion.asistencias.all().delete()
        sesion.delete()
        messages.success(request, 'Sesión eliminada.')
    return redirect('cohortes_detalle', pk=pk)


@permiso_required('cohortes.desactivar')
def desactivar(request, pk):
    cohorte = get_object_or_404(Cohorte, pk=pk)
    if request.method == 'POST':
        cohorte.activo = 0
        cohorte.save()
        messages.success(request, f'Cohorte "{cohorte.nombre}" desactivada.')
    next_url = request.POST.get('next')
    if next_url == 'detalle':
        return redirect('cohortes_detalle', pk=pk)
    return redirect('cohortes_lista')


@permiso_required('cohortes.desactivar')
def activar(request, pk):
    cohorte = get_object_or_404(Cohorte, pk=pk)
    if request.method == 'POST':
        cohorte.activo = 1
        cohorte.save()
        messages.success(request, f'Cohorte "{cohorte.nombre}" activada.')
    next_url = request.POST.get('next')
    if next_url == 'detalle':
        return redirect('cohortes_detalle', pk=pk)
    return redirect('cohortes_lista')