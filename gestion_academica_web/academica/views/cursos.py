from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..decorators import rol_required, get_usuario_sesion
from ..models import Curso, Modalidad
from ..forms import CursoForm


@rol_required('admin')
def lista(request):
    cursos = Curso.objects.select_related('modalidad').order_by('nombre')
    return render(request, 'cursos/list.html', {
        'cursos': cursos,
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
def nuevo(request):
    form = CursoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        Curso.objects.create(
            nombre=d['nombre'],
            descripcion=d.get('descripcion') or '',
            modalidad=d['modalidad'],
            horas_totales=d.get('horas_totales') or 0,
            tarifa_estudiante=d.get('tarifa_estudiante') or 0.0,
            condiciones_ingreso=d.get('condiciones_ingreso') or None,
            activo=1,
        )
        messages.success(request, f'Curso "{d["nombre"]}" creado.')
        return redirect('cursos_lista')
    return render(request, 'cursos/form.html', {
        'form': form, 'titulo': 'Nuevo Curso',
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
def editar(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    initial = {
        'nombre': curso.nombre,
        'descripcion': curso.descripcion,
        'modalidad': curso.modalidad,
        'horas_totales': curso.horas_totales,
        'tarifa_estudiante': curso.tarifa_estudiante,
        'condiciones_ingreso': curso.condiciones_ingreso,
    }
    form = CursoForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        curso.nombre = d['nombre']
        curso.descripcion = d.get('descripcion') or ''
        curso.modalidad = d['modalidad']
        curso.horas_totales = d.get('horas_totales') or 0
        curso.tarifa_estudiante = d.get('tarifa_estudiante') or 0.0
        curso.condiciones_ingreso = d.get('condiciones_ingreso') or None
        curso.save()
        messages.success(request, 'Curso actualizado.')
        return redirect('cursos_lista')
    return render(request, 'cursos/form.html', {
        'form': form, 'titulo': 'Editar Curso', 'curso': curso,
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
def desactivar(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == 'POST':
        curso.activo = 0
        curso.save()
        messages.success(request, f'Curso "{curso.nombre}" desactivado.')
    return redirect('cursos_lista')