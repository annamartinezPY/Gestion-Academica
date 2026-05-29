from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..decorators import permiso_required, get_usuario_sesion
from ..models import TipoContratacion, Docente


@permiso_required('tipos_contratacion.ver')
def lista(request):
    tipos = TipoContratacion.objects.filter(activo=1).order_by('nombre')
    return render(request, 'tipos_contratacion/list.html', {
        'tipos': tipos,
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('tipos_contratacion.crear')
def nuevo(request):
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        if not nombre:
            messages.error(request, 'El nombre del tipo de contratación es obligatorio.')
        elif TipoContratacion.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, f'Ya existe un tipo de contratación con el nombre "{nombre}".')
        else:
            TipoContratacion.objects.create(
                nombre=nombre,
                descripcion=descripcion or None,
                activo=1,
            )
            messages.success(request, f'Tipo de contratación "{nombre}" creado.')
    return redirect('tipos_contratacion_lista')


@permiso_required('tipos_contratacion.editar')
def editar(request, pk):
    tipo = get_object_or_404(TipoContratacion, pk=pk)
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        elif TipoContratacion.objects.filter(nombre__iexact=nombre).exclude(pk=pk).exists():
            messages.error(request, f'Ya existe otro tipo de contratación con el nombre "{nombre}".')
        else:
            tipo.nombre = nombre
            tipo.descripcion = descripcion or None
            tipo.save()
            messages.success(request, 'Tipo de contratación actualizado.')
    return redirect('tipos_contratacion_lista')


@permiso_required('tipos_contratacion.desactivar')
def eliminar(request, pk):
    tipo = get_object_or_404(TipoContratacion, pk=pk)
    if request.method == 'POST':
        if Docente.objects.filter(tipo_contratacion=tipo).exists():
            messages.error(
                request,
                f'No se puede desactivar: el tipo "{tipo.nombre}" está asignado a docentes.'
            )
        else:
            nombre = tipo.nombre
            tipo.activo = 0
            tipo.save()
            messages.success(request, f'Tipo de contratación "{nombre}" desactivado.')
    return redirect('tipos_contratacion_lista')
