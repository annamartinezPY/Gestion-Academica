from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..decorators import rol_required, get_usuario_sesion
from ..models import Cohorte, Sesion, Docente, Inscripcion
from ..forms import CohorteForm, SesionForm


@rol_required('admin')
def lista(request):
    cohortes = Cohorte.objects.select_related('curso__modalidad').order_by('-fecha_inicio')
    return render(request, 'cohortes/list.html', {
        'cohortes': cohortes,
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
def nueva(request):
    form = CohorteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        Cohorte.objects.create(
            nombre=d['nombre'], curso=d['curso'],
            fecha_inicio=d['fecha_inicio'], fecha_fin=d['fecha_fin'],
            cupo_maximo=d['cupo_maximo'], activo=1,
        )
        messages.success(request, f'Cohorte "{d["nombre"]}" creada.')
        return redirect('cohortes_lista')
    return render(request, 'cohortes/form.html', {
        'form': form, 'titulo': 'Nueva Cohorte',
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
def editar(request, pk):
    cohorte = get_object_or_404(Cohorte.objects.select_related('curso'), pk=pk)
    initial = {
        'nombre': cohorte.nombre, 'curso': cohorte.curso,
        'fecha_inicio': cohorte.fecha_inicio, 'fecha_fin': cohorte.fecha_fin,
        'cupo_maximo': cohorte.cupo_maximo,
    }
    form = CohorteForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        cohorte.nombre = d['nombre']
        cohorte.curso = d['curso']
        cohorte.fecha_inicio = d['fecha_inicio']
        cohorte.fecha_fin = d['fecha_fin']
        cohorte.cupo_maximo = d['cupo_maximo']
        cohorte.save()
        messages.success(request, 'Cohorte actualizada.')
        return redirect('cohortes_lista')
    return render(request, 'cohortes/form.html', {
        'form': form, 'titulo': 'Editar Cohorte', 'cohorte': cohorte,
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
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


@rol_required('admin')
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


@rol_required('admin')
def eliminar_sesion(request, pk, sesion_pk):
    sesion = get_object_or_404(Sesion, pk=sesion_pk, cohorte_id=pk)
    if request.method == 'POST':
        sesion.asistencias.all().delete()
        sesion.delete()
        messages.success(request, 'Sesión eliminada.')
    return redirect('cohortes_detalle', pk=pk)


@rol_required('admin')
def desactivar(request, pk):
    cohorte = get_object_or_404(Cohorte, pk=pk)
    if request.method == 'POST':
        cohorte.activo = 0
        cohorte.save()
        messages.success(request, f'Cohorte "{cohorte.nombre}" desactivada.')
    return redirect('cohortes_lista')