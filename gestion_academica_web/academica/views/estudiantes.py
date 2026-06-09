from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from ..decorators import permiso_required, hash_password, get_usuario_sesion
from ..models import Estudiante, Usuario, Rol, Inscripcion, PagoEstudiante
from ..forms import EstudianteForm


@permiso_required('estudiantes.ver')
def lista(request):
    qs = Estudiante.objects.select_related('usuario').order_by('usuario__apellido')
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(usuario__nombre__icontains=q) |
            Q(usuario__apellido__icontains=q) |
            Q(usuario__email__icontains=q) |
            Q(documento__icontains=q)
        )
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'estudiantes/list.html', {
        'estudiantes': page_obj,
        'page_obj': page_obj,
        'q': q,
        'querystring': f'q={q}' if q else '',
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('estudiantes.editar')
def editar(request, pk):
    estudiante = get_object_or_404(Estudiante.objects.select_related('usuario'), pk=pk)
    initial = {
        'nombre': estudiante.usuario.nombre,
        'apellido': estudiante.usuario.apellido,
        'email': estudiante.usuario.email,
        'documento': estudiante.documento,
        'telefono': estudiante.telefono,
        'fecha_nacimiento': estudiante.fecha_nacimiento or '',
        'direccion_residencia': estudiante.direccion_residencia or '',
    }
    form = EstudianteForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        u = estudiante.usuario
        u.nombre = d['nombre']
        u.apellido = d['apellido']
        u.email = d['email']
        if d.get('password'):
            u.password = hash_password(d['password'])
        u.save()
        estudiante.documento = d.get('documento') or None
        estudiante.telefono = d.get('telefono') or None
        estudiante.fecha_nacimiento = d.get('fecha_nacimiento') or None
        estudiante.direccion_residencia = d.get('direccion_residencia') or None
        estudiante.save()
        messages.success(request, 'Estudiante actualizado.')
        return redirect('estudiantes_lista')
    return render(request, 'estudiantes/form.html', {
        'form': form, 'titulo': 'Editar Estudiante', 'estudiante': estudiante,
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('estudiantes.ver')
def detalle(request, pk):
    estudiante = get_object_or_404(Estudiante.objects.select_related('usuario'), pk=pk)
    inscripciones = estudiante.inscripciones.select_related(
        'cohorte__curso'
    ).order_by('-fecha_inscripcion')
    pagos = PagoEstudiante.objects.filter(
        inscripcion__estudiante=estudiante
    ).select_related('inscripcion__cohorte__curso').order_by('-fecha_pago')
    return render(request, 'estudiantes/detail.html', {
        'estudiante': estudiante, 'inscripciones': inscripciones, 'pagos': pagos,
        'usuario': get_usuario_sesion(request),
    })