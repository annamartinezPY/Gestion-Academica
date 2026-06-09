"""Gestión central de usuarios (banco de creación).

El administrador puede dar de alta cualquier tipo de usuario desde un único
formulario. Según el rol elegido, el formulario muestra los campos específicos
del perfil correspondiente (docente, estudiante, tesorero) o sólo los campos
base (admin).
"""
import re
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction

from ..decorators import permiso_required, hash_password, get_usuario_sesion
from ..models import (
    Usuario, Rol,
    Docente, Estudiante, Tesorero,
    Institucion, NivelEducativo, TipoContratacion,
)


EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def _proximo_legajo_docente():
    """Calcula el próximo legajo numérico autoincremental."""
    existentes = []
    for leg in Docente.objects.exclude(legajo_interno__isnull=True).values_list('legajo_interno', flat=True):
        if leg and str(leg).isdigit():
            existentes.append(int(leg))
    return str(max(existentes) + 1) if existentes else '1'


def _parse_tarifa(valor):
    """Convierte '1.500.000' o '1500000' → 1500000.0 (acepta vacío como 0)."""
    if not valor:
        return 0.0
    limpio = str(valor).replace('.', '').replace(',', '').replace(' ', '')
    if not limpio.isdigit():
        return None  # marcador de error
    return float(limpio)


@permiso_required('usuarios.ver')
def lista(request):
    """Listado unificado de usuarios con filtro por rol."""
    rol_filtro = (request.GET.get('rol') or '').strip()
    q = (request.GET.get('q') or '').strip()

    qs = Usuario.objects.select_related('rol').order_by('-id')
    if rol_filtro:
        qs = qs.filter(rol__nombre=rol_filtro)
    if q:
        qs = qs.filter(nombre__icontains=q) | qs.filter(apellido__icontains=q) | qs.filter(email__icontains=q)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    roles = Rol.objects.filter(activo=1).order_by('nombre')

    return render(request, 'usuarios/lista.html', {
        'usuarios_lista': page_obj,
        'page_obj': page_obj,
        'roles': roles,
        'rol_filtro': rol_filtro,
        'q': q,
        'querystring': '&'.join(
            ([f'q={q}'] if q else []) + ([f'rol={rol_filtro}'] if rol_filtro else [])
        ),
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('usuarios.crear')
def nuevo(request):
    """Banco de creación de usuario: un único formulario con secciones dinámicas."""
    roles = Rol.objects.filter(activo=1).order_by('nombre')
    instituciones = Institucion.objects.filter(activo=1).order_by('nombre')
    niveles_educativos = NivelEducativo.objects.filter(activo=1).order_by('nombre')
    tipos_contratacion = TipoContratacion.objects.filter(activo=1).order_by('nombre')

    # Valores iniciales (preview del próximo legajo de docente)
    proximo_legajo = _proximo_legajo_docente()

    ctx = {
        'roles': roles,
        'instituciones': instituciones,
        'niveles_educativos': niveles_educativos,
        'tipos_contratacion': tipos_contratacion,
        'proximo_legajo': proximo_legajo,
        'form_data': {},  # repopular en caso de error
        'usuario': get_usuario_sesion(request),
    }

    if request.method != 'POST':
        return render(request, 'usuarios/nuevo.html', ctx)

    # ── POST ──────────────────────────────────────────────────────────────
    data = request.POST
    files = request.FILES
    ctx['form_data'] = data  # repopular el form si hay error

    nombre   = (data.get('nombre') or '').strip()
    apellido = (data.get('apellido') or '').strip()
    email    = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()
    rol_id   = data.get('rol_id') or ''
    forzar_cambio = data.get('forzar_cambio_password') == 'on'

    # Validaciones base
    errores = []
    if not nombre or not apellido:
        errores.append('Nombre y apellido son obligatorios.')
    if not email or not EMAIL_RE.match(email):
        errores.append('El email no es válido.')
    if not password or len(password) < 6:
        errores.append('La contraseña debe tener al menos 6 caracteres.')
    if not rol_id:
        errores.append('Debe seleccionar un rol.')

    try:
        rol = Rol.objects.get(pk=rol_id, activo=1)
    except (Rol.DoesNotExist, ValueError):
        errores.append('Rol inválido.')
        rol = None

    if Usuario.objects.filter(email=email).exists():
        errores.append(f'Ya existe un usuario con el email "{email}".')

    if errores:
        for e in errores:
            messages.error(request, e)
        return render(request, 'usuarios/nuevo.html', ctx)

    # Crear el usuario y el perfil en una transacción.
    try:
        with transaction.atomic():
            usuario = Usuario.objects.create(
                nombre=nombre,
                apellido=apellido,
                email=email,
                password=hash_password(password),
                rol=rol,
                activo=1,
                must_change_password=1 if forzar_cambio else 0,
            )

            if rol.nombre == 'docente':
                tarifa = _parse_tarifa(data.get('tarifa_hora') or '0')
                if tarifa is None:
                    raise ValueError('La tarifa debe ser un número entero en guaraníes.')
                Docente.objects.create(
                    usuario=usuario,
                    especialidad=(data.get('especialidad') or '').strip(),
                    tarifa_hora=tarifa,
                    telefono=(data.get('telefono') or '').strip() or None,
                    cedula=(data.get('cedula') or '').strip() or None,
                    ruc=(data.get('ruc') or '').strip() or None,
                    foto=files.get('foto') or None,
                    biografia=(data.get('biografia') or '').strip() or None,
                    areas_experiencia=(data.get('areas_experiencia') or '').strip() or None,
                    trayectoria_academica=(data.get('trayectoria_academica') or '').strip() or None,
                    linkedin_url=(data.get('linkedin_url') or '').strip() or None,
                    otras_redes=(data.get('otras_redes') or '').strip() or None,
                    nivel_educativo_id=(data.get('nivel_educativo') or None) or None,
                    legajo_interno=_proximo_legajo_docente(),
                    tipo_contratacion_id=(data.get('tipo_contratacion') or None) or None,
                )

            elif rol.nombre == 'estudiante':
                Estudiante.objects.create(
                    usuario=usuario,
                    documento=(data.get('documento') or '').strip() or None,
                    telefono=(data.get('telefono') or '').strip() or None,
                    fecha_nacimiento=(data.get('fecha_nacimiento') or '').strip() or None,
                    direccion_residencia=(data.get('direccion_residencia') or '').strip() or None,
                )

            elif rol.nombre == 'tesorero':
                Tesorero.objects.create(
                    usuario=usuario,
                    institucion_id=(data.get('institucion') or None) or None,
                    cedula=(data.get('cedula') or '').strip() or None,
                    ruc=(data.get('ruc') or '').strip() or None,
                    fecha_nacimiento=(data.get('fecha_nacimiento') or '').strip() or None,
                    cargo=(data.get('cargo') or '').strip() or None,
                )
            # admin u otro rol no requiere perfil extendido

        messages.success(request, f'Usuario "{nombre} {apellido}" creado correctamente como {rol.nombre}.')
        return redirect('usuarios_lista')

    except Exception as e:
        messages.error(request, f'No se pudo crear el usuario: {e}')
        return render(request, 'usuarios/nuevo.html', ctx)
