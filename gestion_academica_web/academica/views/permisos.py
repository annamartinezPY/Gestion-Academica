from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from ..decorators import permiso_required, get_usuario_sesion
from ..models import Rol, Permiso, RolPermiso, Usuario

# Roles del sistema que no se pueden desactivar ni eliminar (núcleo del RBAC)
ROLES_PROTEGIDOS = {'admin'}


@permiso_required('permisos.gestionar')
def lista_roles(request):
    """Listado y creación de roles."""
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip().lower().replace(' ', '_')
        descripcion = request.POST.get('descripcion', '').strip()
        if not nombre:
            messages.error(request, 'El nombre del rol es obligatorio.')
        elif Rol.objects.filter(nombre=nombre).exists():
            messages.error(request, f'Ya existe un rol con el nombre "{nombre}".')
        else:
            Rol.objects.create(nombre=nombre, descripcion=descripcion, activo=1)
            messages.success(request, f'Rol "{nombre}" creado. Asigná los permisos correspondientes.')
            return redirect('permisos_roles')

    incluir_inactivos = request.GET.get('inactivos') == '1'
    qs = Rol.objects.prefetch_related('permisos__permiso')
    if not incluir_inactivos:
        qs = qs.filter(activo=1)
    roles = qs.order_by('-activo', 'nombre').annotate(
        usuarios_activos=Count('usuario', filter=Q(usuario__activo=1))
    )

    return render(request, 'permisos/roles.html', {
        'roles': roles,
        'incluir_inactivos': incluir_inactivos,
        'roles_protegidos': ROLES_PROTEGIDOS,
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('permisos.gestionar')
def editar_rol(request, rol_id):
    """Actualiza nombre y descripción de un rol existente."""
    rol = get_object_or_404(Rol, pk=rol_id)

    if request.method != 'POST':
        return redirect('permisos_roles')

    nombre_actual = rol.nombre
    nombre_nuevo = request.POST.get('nombre', '').strip().lower().replace(' ', '_')
    descripcion = request.POST.get('descripcion', '').strip()

    if not nombre_nuevo:
        messages.error(request, 'El nombre del rol es obligatorio.')
        return redirect('permisos_roles')

    # No permitir renombrar roles protegidos del núcleo
    if nombre_actual in ROLES_PROTEGIDOS and nombre_nuevo != nombre_actual:
        messages.error(request, f'El rol "{nombre_actual}" es del sistema y no puede renombrarse.')
        return redirect('permisos_roles')

    if nombre_nuevo != nombre_actual and Rol.objects.filter(nombre=nombre_nuevo).exclude(pk=rol_id).exists():
        messages.error(request, f'Ya existe un rol con el nombre "{nombre_nuevo}".')
        return redirect('permisos_roles')

    rol.nombre = nombre_nuevo
    rol.descripcion = descripcion
    rol.save()
    messages.success(request, f'Rol "{nombre_nuevo}" actualizado correctamente.')
    return redirect('permisos_roles')


@permiso_required('permisos.gestionar')
def toggle_activo(request, rol_id):
    """Activa o desactiva un rol. Si el rol está inactivo, no se pueden loguear sus usuarios."""
    rol = get_object_or_404(Rol, pk=rol_id)

    if request.method != 'POST':
        return redirect('permisos_roles')

    if rol.nombre in ROLES_PROTEGIDOS:
        messages.error(request, f'El rol "{rol.nombre}" es del sistema y no puede desactivarse.')
        return redirect('permisos_roles')

    if rol.activo:
        # Vamos a desactivarlo: advertir si hay usuarios activos asociados
        usuarios_activos = Usuario.objects.filter(rol=rol, activo=1).count()
        rol.activo = 0
        rol.save()
        msg = f'Rol "{rol.nombre}" desactivado.'
        if usuarios_activos:
            msg += (f' Atención: {usuarios_activos} usuario{"s" if usuarios_activos != 1 else ""} '
                    f'activo{"s" if usuarios_activos != 1 else ""} '
                    f'con este rol no podrá{"n" if usuarios_activos != 1 else ""} iniciar sesión.')
            messages.warning(request, msg)
        else:
            messages.success(request, msg)
    else:
        rol.activo = 1
        rol.save()
        messages.success(request, f'Rol "{rol.nombre}" reactivado.')

    return redirect('permisos_roles')


@permiso_required('permisos.gestionar')
def gestionar_rol(request, rol_id):
    """Pantalla de asignación/eliminación de permisos por rol, agrupados por módulo."""
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
