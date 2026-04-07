from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..decorators import rol_required, hash_password, get_usuario_sesion
from ..models import Docente, Usuario, Rol
from ..forms import DocenteForm


@rol_required('admin')
def lista(request):
    docentes = Docente.objects.select_related('usuario__rol').order_by('usuario__apellido')
    return render(request, 'docentes/list.html', {
        'docentes': docentes,
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
def nuevo(request):
    form = DocenteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        if not d.get('password'):
            messages.error(request, 'La contraseña es obligatoria al crear un docente.')
        elif Usuario.objects.filter(email=d['email']).exists():
            messages.error(request, 'Ya existe un usuario con ese email.')
        else:
            rol = Rol.objects.get(nombre='docente')
            usuario = Usuario.objects.create(
                nombre=d['nombre'], apellido=d['apellido'],
                email=d['email'], password=hash_password(d['password']),
                rol=rol, activo=1,
            )
            Docente.objects.create(
                usuario=usuario,
                especialidad=d.get('especialidad') or '',
                tarifa_hora=d.get('tarifa_hora') or 0.0,
            )
            messages.success(request, f'Docente {d["nombre"]} {d["apellido"]} registrado.')
            return redirect('docentes_lista')
    return render(request, 'docentes/form.html', {
        'form': form, 'titulo': 'Nuevo Docente',
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
def editar(request, pk):
    docente = get_object_or_404(Docente.objects.select_related('usuario'), pk=pk)
    initial = {
        'nombre': docente.usuario.nombre,
        'apellido': docente.usuario.apellido,
        'email': docente.usuario.email,
        'especialidad': docente.especialidad,
        'tarifa_hora': docente.tarifa_hora,
    }
    form = DocenteForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        u = docente.usuario
        u.nombre = d['nombre']
        u.apellido = d['apellido']
        u.email = d['email']
        if d.get('password'):
            u.password = hash_password(d['password'])
        u.save()
        docente.especialidad = d.get('especialidad') or ''
        docente.tarifa_hora = d.get('tarifa_hora') or 0.0
        docente.save()
        messages.success(request, 'Docente actualizado.')
        return redirect('docentes_lista')
    return render(request, 'docentes/form.html', {
        'form': form, 'titulo': 'Editar Docente', 'docente': docente,
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
def detalle(request, pk):
    docente = get_object_or_404(Docente.objects.select_related('usuario'), pk=pk)
    sesiones = docente.sesiones.select_related('cohorte__curso').order_by('-fecha')
    pagos = docente.pagos.select_related('cohorte__curso').order_by('-fecha_pago')

    cohortes_ids = sesiones.values_list('cohorte_id', flat=True).distinct()
    from ..models import Cohorte
    cohortes = Cohorte.objects.filter(id__in=cohortes_ids).select_related('curso')

    return render(request, 'docentes/detail.html', {
        'docente': docente, 'sesiones': sesiones,
        'pagos': pagos, 'cohortes': cohortes,
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
def desactivar(request, pk):
    docente = get_object_or_404(Docente.objects.select_related('usuario'), pk=pk)
    if request.method == 'POST':
        docente.usuario.activo = 0
        docente.usuario.save()
        messages.success(request, f'Docente {docente.usuario.nombre_completo} desactivado.')
    return redirect('docentes_lista')