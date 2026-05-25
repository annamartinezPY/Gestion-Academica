from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..decorators import permiso_required, get_usuario_sesion
from ..models import Modalidad, CondicionInscripcion


@permiso_required('config.editar')
def index(request):
    modalidades = Modalidad.objects.order_by('nombre')
    condiciones = CondicionInscripcion.objects.filter(activo=1).order_by('nombre')
    return render(request, 'config_curso/index.html', {
        'modalidades': modalidades,
        'condiciones': condiciones,
        'usuario': get_usuario_sesion(request),
    })


# ── Modalidades ──────────────────────────────────────────────────────────────

@permiso_required('config.editar')
def nueva_modalidad(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        if not nombre:
            messages.error(request, 'El nombre de la modalidad es obligatorio.')
        elif Modalidad.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, f'Ya existe una modalidad con el nombre "{nombre}".')
        else:
            Modalidad.objects.create(nombre=nombre)
            messages.success(request, f'Modalidad "{nombre}" creada.')
    return redirect('config_curso')


@permiso_required('config.editar')
def editar_modalidad(request, pk):
    modalidad = get_object_or_404(Modalidad, pk=pk)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        elif Modalidad.objects.filter(nombre__iexact=nombre).exclude(pk=pk).exists():
            messages.error(request, f'Ya existe otra modalidad con el nombre "{nombre}".')
        else:
            modalidad.nombre = nombre
            modalidad.save()
            messages.success(request, 'Modalidad actualizada.')
    return redirect('config_curso')


@permiso_required('config.editar')
def eliminar_modalidad(request, pk):
    modalidad = get_object_or_404(Modalidad, pk=pk)
    if request.method == 'POST':
        if modalidad.curso_set.exists():
            messages.error(request, f'No se puede eliminar: la modalidad "{modalidad.nombre}" tiene cursos asignados.')
        else:
            nombre = modalidad.nombre
            modalidad.delete()
            messages.success(request, f'Modalidad "{nombre}" eliminada.')
    return redirect('config_curso')


# ── Condiciones de inscripción ────────────────────────────────────────────────

@permiso_required('config.editar')
def nueva_condicion(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        if not nombre:
            messages.error(request, 'El nombre de la condición es obligatorio.')
        elif CondicionInscripcion.objects.filter(nombre__iexact=nombre, activo=1).exists():
            messages.error(request, f'Ya existe una condición con el nombre "{nombre}".')
        else:
            CondicionInscripcion.objects.create(nombre=nombre, descripcion=descripcion or None, activo=1)
            messages.success(request, f'Condición "{nombre}" creada.')
    return redirect('config_curso')


@permiso_required('config.editar')
def editar_condicion(request, pk):
    condicion = get_object_or_404(CondicionInscripcion, pk=pk)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        elif CondicionInscripcion.objects.filter(nombre__iexact=nombre, activo=1).exclude(pk=pk).exists():
            messages.error(request, f'Ya existe otra condición con ese nombre.')
        else:
            condicion.nombre = nombre
            condicion.descripcion = descripcion or None
            condicion.save()
            messages.success(request, 'Condición actualizada.')
    return redirect('config_curso')


@permiso_required('config.editar')
def eliminar_condicion(request, pk):
    condicion = get_object_or_404(CondicionInscripcion, pk=pk)
    if request.method == 'POST':
        if condicion.cursos.exists():
            messages.error(request, f'No se puede eliminar: la condición tiene cursos asignados.')
        else:
            nombre = condicion.nombre
            condicion.activo = 0
            condicion.save()
            messages.success(request, f'Condición "{nombre}" desactivada.')
    return redirect('config_curso')
