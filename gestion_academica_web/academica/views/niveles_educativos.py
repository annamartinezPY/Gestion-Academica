from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..decorators import permiso_required, get_usuario_sesion
from ..models import NivelEducativo, DocenteInstitucion


@permiso_required('docentes.ver')
def lista(request):
    niveles = NivelEducativo.objects.filter(activo=1).order_by('nombre')
    return render(request, 'niveles_educativos/list.html', {
        'niveles': niveles,
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('docentes.editar')
def nuevo(request):
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        if not nombre:
            messages.error(request, 'El nombre del nivel educativo es obligatorio.')
        elif NivelEducativo.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, f'Ya existe un nivel educativo con el nombre "{nombre}".')
        else:
            NivelEducativo.objects.create(
                nombre=nombre,
                descripcion=descripcion or None,
                activo=1,
            )
            messages.success(request, f'Nivel educativo "{nombre}" creado.')
            return redirect('niveles_educativos_lista')
    return redirect('niveles_educativos_lista')


@permiso_required('docentes.editar')
def editar(request, pk):
    nivel = get_object_or_404(NivelEducativo, pk=pk)
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        elif NivelEducativo.objects.filter(nombre__iexact=nombre).exclude(pk=pk).exists():
            messages.error(request, f'Ya existe otro nivel educativo con el nombre "{nombre}".')
        else:
            nivel.nombre = nombre
            nivel.descripcion = descripcion or None
            nivel.save()
            messages.success(request, 'Nivel educativo actualizado.')
    return redirect('niveles_educativos_lista')


@permiso_required('docentes.editar')
def eliminar(request, pk):
    nivel = get_object_or_404(NivelEducativo, pk=pk)
    if request.method == 'POST':
        if DocenteInstitucion.objects.filter(nivel_educativo=nivel).exists():
            messages.error(
                request,
                f'No se puede eliminar: el nivel "{nivel.nombre}" está asignado a docentes.'
            )
        else:
            nombre = nivel.nombre
            nivel.activo = 0
            nivel.save()
            messages.success(request, f'Nivel educativo "{nombre}" desactivado.')
    return redirect('niveles_educativos_lista')
