from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..decorators import permiso_required, get_usuario_sesion
from ..models import Rol, Permiso, RolPermiso


@permiso_required('permisos.gestionar')
def lista_roles(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip().lower().replace(' ', '_')
        descripcion = request.POST.get('descripcion', '').strip()
        if not nombre:
            messages.error(request, 'El nombre del rol es obligatorio.')
        elif Rol.objects.filter(nombre=nombre).exists():
            messages.error(request, f'Ya existe un rol con el nombre "{nombre}".')
        else:
            Rol.objects.create(nombre=nombre, descripcion=descripcion)
            messages.success(request, f'Rol "{nombre}" creado. Asigná los permisos correspondientes.')
            return redirect('permisos_roles')

    roles = Rol.objects.prefetch_related('permisos__permiso').order_by('nombre')
    return render(request, 'permisos/roles.html', {
        'roles': roles,
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('permisos.gestionar')
def gestionar_rol(request, rol_id):
    rol = get_object_or_404(Rol, pk=rol_id)
    todos_permisos = Permiso.objects.order_by('modulo', 'nombre')
    permisos_actuales = set(
        RolPermiso.objects.filter(rol=rol).values_list('permiso_id', flat=True)
    )

    # Agrupar por módulo para la vista
    modulos = {}
    for p in todos_permisos:
        modulos.setdefault(p.modulo, []).append(p)

    if request.method == 'POST':
        nuevos_ids = set(int(x) for x in request.POST.getlist('permisos'))

        # Quitar los que ya no están
        quitar = permisos_actuales - nuevos_ids
        if quitar:
            RolPermiso.objects.filter(rol=rol, permiso_id__in=quitar).delete()

        # Agregar los nuevos
        agregar = nuevos_ids - permisos_actuales
        for pid in agregar:
            RolPermiso.objects.get_or_create(rol=rol, permiso_id=pid)

        messages.success(request, f'Permisos del rol "{rol.nombre}" actualizados.')
        return redirect('permisos_roles')

    return render(request, 'permisos/gestionar.html', {
        'rol': rol,
        'modulos': modulos,
        'permisos_actuales': permisos_actuales,
        'usuario': get_usuario_sesion(request),
    })
