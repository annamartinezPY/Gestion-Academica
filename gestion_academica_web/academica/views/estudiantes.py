from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..decorators import rol_required, hash_password, get_usuario_sesion
from ..models import Estudiante, Usuario, Rol, Inscripcion, PagoEstudiante
from ..forms import EstudianteForm


@rol_required('admin')
def lista(request):
    estudiantes = Estudiante.objects.select_related('usuario').order_by('usuario__apellido')
    return render(request, 'estudiantes/list.html', {
        'estudiantes': estudiantes,
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
def nuevo(request):
    form = EstudianteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        if not d.get('password'):
            messages.error(request, 'La contraseña es obligatoria al crear un estudiante.')
        elif Usuario.objects.filter(email=d['email']).exists():
            messages.error(request, 'Ya existe un usuario con ese email.')
        else:
            rol = Rol.objects.get(nombre='estudiante')
            usuario = Usuario.objects.create(
                nombre=d['nombre'], apellido=d['apellido'],
                email=d['email'], password=hash_password(d['password']),
                rol=rol, activo=1,
            )
            Estudiante.objects.create(
                usuario=usuario,
                documento=d.get('documento') or None,
                telefono=d.get('telefono') or None,
            )
            messages.success(request, f'Estudiante {d["nombre"]} {d["apellido"]} registrado.')
            return redirect('estudiantes_lista')
    return render(request, 'estudiantes/form.html', {
        'form': form, 'titulo': 'Nuevo Estudiante',
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
def editar(request, pk):
    estudiante = get_object_or_404(Estudiante.objects.select_related('usuario'), pk=pk)
    initial = {
        'nombre': estudiante.usuario.nombre,
        'apellido': estudiante.usuario.apellido,
        'email': estudiante.usuario.email,
        'documento': estudiante.documento,
        'telefono': estudiante.telefono,
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
        estudiante.save()
        messages.success(request, 'Estudiante actualizado.')
        return redirect('estudiantes_lista')
    return render(request, 'estudiantes/form.html', {
        'form': form, 'titulo': 'Editar Estudiante', 'estudiante': estudiante,
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
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