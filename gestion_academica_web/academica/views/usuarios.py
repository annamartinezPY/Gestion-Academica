"""Gestión central de usuarios (banco de creación).

El administrador puede dar de alta cualquier tipo de usuario desde un único
formulario. Según el rol elegido, el formulario muestra los campos específicos
del perfil correspondiente (docente, estudiante, tesorero) o sólo los campos
base (admin).
"""
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction

from ..decorators import permiso_required, hash_password, get_usuario_sesion
from ..models import (
    Usuario, Rol,
    Docente, Estudiante, Tesorero,
    Institucion, NivelEducativo, TipoContratacion,
)


def _fmt_guaranies(valor):
    """50000 → '50.000' (entero con separador de miles tipo guaraní)."""
    try:
        return f'{int(round(float(valor or 0))):,}'.replace(',', '.')
    except (TypeError, ValueError):
        return '0'


NOMBRE_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s'-]+$")
SOLO_DIGITOS_RE = re.compile(r'^\d+$')


# ── Validadores reutilizables ───────────────────────────────────────────

def _v_nombre(valor, etiqueta):
    """Solo letras (con tildes/ñ), espacios, apóstrofo y guión."""
    valor = (valor or '').strip()
    if not valor:
        return f'El {etiqueta} es obligatorio.'
    if not NOMBRE_RE.match(valor):
        return f'El {etiqueta} sólo puede contener letras.'
    return None


def _v_email(valor):
    valor = (valor or '').strip().lower()
    if not valor:
        return 'El email es obligatorio.'
    if '@' not in valor or '.' not in valor:
        return 'El email debe contener "@" y "." (Ej: usuario@dominio.com).'
    return None


def _v_documento(valor, etiqueta='documento'):
    """Solo dígitos. Opcional."""
    valor = (valor or '').strip()
    if not valor:
        return None
    if not SOLO_DIGITOS_RE.match(valor):
        return f'El {etiqueta} debe contener sólo números, sin caracteres especiales.'
    return None


def _v_telefono(valor):
    """Solo dígitos, mínimo 10. Opcional."""
    valor = (valor or '').strip()
    if not valor:
        return None
    if not SOLO_DIGITOS_RE.match(valor):
        return 'El teléfono debe contener sólo números, sin caracteres especiales.'
    if len(valor) < 10:
        return 'El teléfono debe tener al menos 10 dígitos.'
    return None


def _v_fecha_nacimiento(valor):
    """No puede ser mayor al año actual. Opcional."""
    valor = (valor or '').strip()
    if not valor:
        return None
    from datetime import date
    try:
        fn = date.fromisoformat(valor[:10])
    except ValueError:
        return 'La fecha de nacimiento tiene formato inválido.'
    if fn > date.today():
        return 'La fecha de nacimiento no puede ser mayor al año actual.'
    return None


def _validar_perfil(data, rol_nombre):
    """Devuelve lista de errores de validación según el rol."""
    errores = []
    e = _v_nombre(data.get('nombre'), 'nombre');     errores.append(e) if e else None
    e = _v_nombre(data.get('apellido'), 'apellido'); errores.append(e) if e else None
    e = _v_email(data.get('email'));                 errores.append(e) if e else None

    if rol_nombre == 'docente':
        e = _v_documento(data.get('cedula'), 'cédula');  errores.append(e) if e else None
        e = _v_telefono(data.get('telefono'));            errores.append(e) if e else None
    elif rol_nombre == 'estudiante':
        e = _v_documento(data.get('documento'), 'documento'); errores.append(e) if e else None
        e = _v_telefono(data.get('telefono'));                 errores.append(e) if e else None
        e = _v_fecha_nacimiento(data.get('fecha_nacimiento')); errores.append(e) if e else None
    elif rol_nombre == 'tesorero':
        e = _v_documento(data.get('cedula'), 'cédula');        errores.append(e) if e else None
        e = _v_fecha_nacimiento(data.get('fecha_nacimiento')); errores.append(e) if e else None
    return errores


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
    if not password or len(password) < 6:
        errores.append('La contraseña debe tener al menos 6 caracteres.')
    if not rol_id:
        errores.append('Debe seleccionar un rol.')

    try:
        rol = Rol.objects.get(pk=rol_id, activo=1)
    except (Rol.DoesNotExist, ValueError):
        errores.append('Rol inválido.')
        rol = None

    # Validaciones de formato (nombre, apellido, email, documento, teléfono, fecha)
    if rol:
        errores.extend(_validar_perfil(data, rol.nombre))

    if email and Usuario.objects.filter(email=email).exists():
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


@permiso_required('usuarios.editar')
def editar(request, pk):
    """Edita los datos del usuario y de su perfil específico (según rol).
    El rol NO se cambia desde acá (cambiar de rol implica recrear el perfil)."""
    usuario_obj = get_object_or_404(Usuario.objects.select_related('rol'), pk=pk)
    rol_nombre = usuario_obj.rol.nombre

    # Cargar el perfil específico según rol (puede no existir)
    docente = None
    estudiante = None
    tesorero = None
    if rol_nombre == 'docente':
        docente = Docente.objects.filter(usuario=usuario_obj).first()
    elif rol_nombre == 'estudiante':
        estudiante = Estudiante.objects.filter(usuario=usuario_obj).first()
    elif rol_nombre == 'tesorero':
        tesorero = Tesorero.objects.filter(usuario=usuario_obj).first()

    # Pre-llenar form_data con los valores actuales
    form_data = {
        'nombre': usuario_obj.nombre,
        'apellido': usuario_obj.apellido,
        'email': usuario_obj.email,
    }
    if docente:
        form_data.update({
            'especialidad': docente.especialidad or '',
            'tarifa_hora': _fmt_guaranies(docente.tarifa_hora),
            'telefono': docente.telefono or '',
            'cedula': docente.cedula or '',
            'ruc': docente.ruc or '',
            'biografia': docente.biografia or '',
            'areas_experiencia': docente.areas_experiencia or '',
            'trayectoria_academica': docente.trayectoria_academica or '',
            'linkedin_url': docente.linkedin_url or '',
            'otras_redes': docente.otras_redes or '',
            'nivel_educativo': str(docente.nivel_educativo_id or ''),
            'tipo_contratacion': str(docente.tipo_contratacion_id or ''),
            'legajo_interno': docente.legajo_interno or '',
        })
    elif estudiante:
        form_data.update({
            'documento': estudiante.documento or '',
            'telefono': estudiante.telefono or '',
            'fecha_nacimiento': estudiante.fecha_nacimiento or '',
            'direccion_residencia': estudiante.direccion_residencia or '',
        })
    elif tesorero:
        form_data.update({
            'institucion': str(tesorero.institucion_id or ''),
            'cargo': tesorero.cargo or '',
            'cedula': tesorero.cedula or '',
            'ruc': tesorero.ruc or '',
            'fecha_nacimiento': tesorero.fecha_nacimiento or '',
        })

    ctx = {
        'usuario_obj': usuario_obj,
        'rol_nombre': rol_nombre,
        'instituciones': Institucion.objects.filter(activo=1).order_by('nombre'),
        'niveles_educativos': NivelEducativo.objects.filter(activo=1).order_by('nombre'),
        'tipos_contratacion': TipoContratacion.objects.filter(activo=1).order_by('nombre'),
        'form_data': form_data,
        'usuario': get_usuario_sesion(request),
    }

    if request.method != 'POST':
        return render(request, 'usuarios/editar.html', ctx)

    # ── POST ──────────────────────────────────────────────────────────────
    data = request.POST
    files = request.FILES
    ctx['form_data'] = data

    nombre   = (data.get('nombre') or '').strip()
    apellido = (data.get('apellido') or '').strip()
    email    = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()

    errores = list(_validar_perfil(data, rol_nombre))
    if password and len(password) < 6:
        errores.append('La nueva contraseña debe tener al menos 6 caracteres.')
    if email and Usuario.objects.filter(email=email).exclude(pk=usuario_obj.pk).exists():
        errores.append(f'Ya existe otro usuario con el email "{email}".')

    if errores:
        for e in errores:
            messages.error(request, e)
        return render(request, 'usuarios/editar.html', ctx)

    forzar_cambio = data.get('forzar_cambio_password') == 'on'

    try:
        with transaction.atomic():
            usuario_obj.nombre = nombre
            usuario_obj.apellido = apellido
            usuario_obj.email = email
            if password:
                usuario_obj.password = hash_password(password)
            usuario_obj.must_change_password = 1 if forzar_cambio else 0
            usuario_obj.save()

            if rol_nombre == 'docente' and docente:
                tarifa = _parse_tarifa(data.get('tarifa_hora') or '0')
                if tarifa is None:
                    raise ValueError('La tarifa debe ser un número entero en guaraníes.')
                docente.especialidad = (data.get('especialidad') or '').strip()
                docente.tarifa_hora = tarifa
                docente.telefono = (data.get('telefono') or '').strip() or None
                docente.cedula = (data.get('cedula') or '').strip() or None
                docente.ruc = (data.get('ruc') or '').strip() or None
                if files.get('foto'):
                    docente.foto = files['foto']
                docente.biografia = (data.get('biografia') or '').strip() or None
                docente.areas_experiencia = (data.get('areas_experiencia') or '').strip() or None
                docente.trayectoria_academica = (data.get('trayectoria_academica') or '').strip() or None
                docente.linkedin_url = (data.get('linkedin_url') or '').strip() or None
                docente.otras_redes = (data.get('otras_redes') or '').strip() or None
                docente.nivel_educativo_id = (data.get('nivel_educativo') or None) or None
                docente.tipo_contratacion_id = (data.get('tipo_contratacion') or None) or None
                docente.save()

            elif rol_nombre == 'estudiante' and estudiante:
                estudiante.documento = (data.get('documento') or '').strip() or None
                estudiante.telefono = (data.get('telefono') or '').strip() or None
                estudiante.fecha_nacimiento = (data.get('fecha_nacimiento') or '').strip() or None
                estudiante.direccion_residencia = (data.get('direccion_residencia') or '').strip() or None
                estudiante.save()

            elif rol_nombre == 'tesorero' and tesorero:
                tesorero.institucion_id = (data.get('institucion') or None) or None
                tesorero.cargo = (data.get('cargo') or '').strip() or None
                tesorero.cedula = (data.get('cedula') or '').strip() or None
                tesorero.ruc = (data.get('ruc') or '').strip() or None
                tesorero.fecha_nacimiento = (data.get('fecha_nacimiento') or '').strip() or None
                tesorero.save()

        messages.success(request, f'Usuario "{nombre} {apellido}" actualizado correctamente.')
        return redirect('usuarios_lista')

    except Exception as e:
        messages.error(request, f'No se pudo actualizar el usuario: {e}')
        return render(request, 'usuarios/editar.html', ctx)


@permiso_required('usuarios.desactivar')
def toggle_activo(request, pk):
    """Activa o desactiva un usuario."""
    usuario_obj = get_object_or_404(Usuario.objects.select_related('rol'), pk=pk)
    sesion = get_usuario_sesion(request)

    if request.method != 'POST':
        return redirect('usuarios_lista')

    # Evitar que un admin se desactive a sí mismo
    if usuario_obj.id == sesion.get('id') or usuario_obj.id == sesion.get('usuario_id'):
        messages.error(request, 'No podés desactivar tu propio usuario.')
        return redirect('usuarios_lista')

    if usuario_obj.activo:
        usuario_obj.activo = 0
        usuario_obj.save()
        messages.warning(request, f'Usuario "{usuario_obj.nombre_completo}" desactivado.')
    else:
        usuario_obj.activo = 1
        usuario_obj.save()
        messages.success(request, f'Usuario "{usuario_obj.nombre_completo}" reactivado.')

    return redirect('usuarios_lista')
