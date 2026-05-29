from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from ..decorators import permiso_required, hash_password, get_usuario_sesion
from ..models import (
    Docente, Usuario, Rol,
    Institucion, DocenteInstitucion, NivelEducativo,
)
from ..forms import DocenteForm


@permiso_required('docentes.ver')
def lista(request):
    qs = Docente.objects.select_related('usuario__rol').order_by('usuario__apellido')
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(usuario__nombre__icontains=q) |
            Q(usuario__apellido__icontains=q) |
            Q(usuario__email__icontains=q) |
            Q(especialidad__icontains=q) |
            Q(legajo_interno__icontains=q)
        )
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'docentes/list.html', {
        'docentes': page_obj,
        'page_obj': page_obj,
        'q': q,
        'querystring': f'q={q}' if q else '',
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('docentes.crear')
def nuevo(request):
    form = DocenteForm(request.POST or None, request.FILES or None)
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
                must_change_password=1 if d.get('forzar_cambio_password') else 0,
            )
            Docente.objects.create(
                usuario=usuario,
                especialidad=d.get('especialidad') or '',
                tarifa_hora=d.get('tarifa_hora') or 0.0,
                telefono=d.get('telefono') or None,
                cedula=d.get('cedula') or None,
                ruc=d.get('ruc') or None,
                foto=d.get('foto') or None,
                biografia=d.get('biografia') or None,
                areas_experiencia=d.get('areas_experiencia') or None,
                trayectoria_academica=d.get('trayectoria_academica') or None,
                linkedin_url=d.get('linkedin_url') or None,
                otras_redes=d.get('otras_redes') or None,
                nivel_educativo=d.get('nivel_educativo') or None,
                legajo_interno=d.get('legajo_interno') or None,
                tipo_contratacion=d.get('tipo_contratacion') or None,
            )
            messages.success(request, f'Docente {d["nombre"]} {d["apellido"]} registrado.')
            return redirect('docentes_lista')
    return render(request, 'docentes/form.html', {
        'form': form, 'titulo': 'Nuevo Docente',
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('docentes.editar')
def editar(request, pk):
    docente = get_object_or_404(Docente.objects.select_related('usuario'), pk=pk)
    initial = {
        'nombre': docente.usuario.nombre,
        'apellido': docente.usuario.apellido,
        'email': docente.usuario.email,
        'especialidad': docente.especialidad,
        'tarifa_hora': docente.tarifa_hora,
        'telefono': docente.telefono or '',
        'cedula': docente.cedula or '',
        'ruc': docente.ruc or '',
        'forzar_cambio_password': bool(docente.usuario.must_change_password),
        'biografia': docente.biografia or '',
        'areas_experiencia': docente.areas_experiencia or '',
        'trayectoria_academica': docente.trayectoria_academica or '',
        'linkedin_url': docente.linkedin_url or '',
        'otras_redes': docente.otras_redes or '',
        'nivel_educativo': docente.nivel_educativo_id or '',
        'legajo_interno': docente.legajo_interno or '',
        'tipo_contratacion': docente.tipo_contratacion_id or '',
    }
    form = DocenteForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        u = docente.usuario
        u.nombre = d['nombre']
        u.apellido = d['apellido']
        u.email = d['email']
        if d.get('password'):
            u.password = hash_password(d['password'])
            u.must_change_password = 1 if d.get('forzar_cambio_password') else 0
        u.save()
        docente.especialidad = d.get('especialidad') or ''
        docente.tarifa_hora = d.get('tarifa_hora') or 0.0
        docente.telefono = d.get('telefono') or None
        docente.cedula = d.get('cedula') or None
        docente.ruc = d.get('ruc') or None
        if d.get('foto'):
            docente.foto = d['foto']
        docente.biografia = d.get('biografia') or None
        docente.areas_experiencia = d.get('areas_experiencia') or None
        docente.trayectoria_academica = d.get('trayectoria_academica') or None
        docente.linkedin_url = d.get('linkedin_url') or None
        docente.otras_redes = d.get('otras_redes') or None
        docente.nivel_educativo = d.get('nivel_educativo') or None
        docente.legajo_interno = d.get('legajo_interno') or None
        docente.tipo_contratacion = d.get('tipo_contratacion') or None
        docente.save()
        messages.success(request, 'Docente actualizado.')
        return redirect('docentes_lista')
    return render(request, 'docentes/form.html', {
        'form': form, 'titulo': 'Editar Docente', 'docente': docente,
        'usuario': get_usuario_sesion(request),
    })


def perfil_completo(request, pk):
    """Vista pública del perfil profesional del docente (la que ve el estudiante).
    Requiere sesión iniciada para evitar exposición a anónimos."""
    if not request.session.get('usuario_id'):
        return redirect('login')

    from ..models import Cohorte, Curso, Inscripcion
    docente = get_object_or_404(
        Docente.objects.select_related('usuario'),
        pk=pk, usuario__activo=1,
    )

    # Cursos que dicta: vía sesiones → cohortes → cursos (activos, sin duplicar)
    cursos_ids = (docente.sesiones
                  .filter(cohorte__activo=1, cohorte__curso__activo=1)
                  .values_list('cohorte__curso_id', flat=True)
                  .distinct())
    cursos = (Curso.objects.filter(id__in=cursos_ids)
              .select_related('modalidad', 'institucion'))

    # Vínculos institucionales (con nivel educativo)
    vinculos = (DocenteInstitucion.objects
                .filter(docente=docente)
                .select_related('institucion', 'nivel_educativo')
                .order_by('institucion__nombre'))

    # ¿El estudiante actual está inscrito en alguna cohorte de este docente?
    usuario_sesion = get_usuario_sesion(request)
    inscrito_con_docente = False
    if usuario_sesion['rol'] == 'estudiante' and usuario_sesion.get('perfil_id'):
        cohortes_del_docente = (docente.sesiones
                                .values_list('cohorte_id', flat=True)
                                .distinct())
        inscrito_con_docente = Inscripcion.objects.filter(
            estudiante_id=usuario_sesion['perfil_id'],
            cohorte_id__in=cohortes_del_docente,
            estado='activa',
        ).exists()

    return render(request, 'docentes/perfil_completo.html', {
        'docente': docente,
        'cursos': cursos,
        'vinculos': vinculos,
        'inscrito_con_docente': inscrito_con_docente,
        'usuario': usuario_sesion,
    })


@permiso_required('docentes.ver')
def detalle(request, pk):
    docente = get_object_or_404(Docente.objects.select_related('usuario'), pk=pk)
    sesiones = docente.sesiones.select_related('cohorte__curso').order_by('-fecha')
    pagos = docente.pagos.select_related('cohorte__curso').order_by('-fecha_pago')

    cohortes_ids = sesiones.values_list('cohorte_id', flat=True).distinct()
    from ..models import Cohorte
    cohortes = Cohorte.objects.filter(id__in=cohortes_ids).select_related('curso')

    vinculos = (DocenteInstitucion.objects
                .filter(docente=docente)
                .select_related('institucion', 'nivel_educativo')
                .order_by('institucion__nombre'))
    inst_vinculadas_ids = set(vinculos.values_list('institucion_id', flat=True))
    instituciones_disponibles = (Institucion.objects.filter(activo=1)
                                 .exclude(id__in=inst_vinculadas_ids)
                                 .order_by('nombre'))
    niveles = NivelEducativo.objects.filter(activo=1).order_by('nombre')

    return render(request, 'docentes/detail.html', {
        'docente': docente, 'sesiones': sesiones,
        'pagos': pagos, 'cohortes': cohortes,
        'vinculos': vinculos,
        'instituciones_disponibles': instituciones_disponibles,
        'niveles': niveles,
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('docentes.editar')
def institucion_vincular(request, pk):
    """Vincula una institución al docente con email institucional y nivel educativo."""
    docente = get_object_or_404(Docente, pk=pk)
    if request.method != 'POST':
        return redirect('docentes_detalle', pk=pk)

    inst_id = request.POST.get('institucion_id')
    email_inst = (request.POST.get('email_institucional') or '').strip() or None
    nivel_id = request.POST.get('nivel_educativo_id') or None

    try:
        institucion = Institucion.objects.get(pk=inst_id, activo=1)
    except Institucion.DoesNotExist:
        messages.error(request, 'Institución no encontrada.')
        return redirect('docentes_detalle', pk=pk)

    nivel = None
    if nivel_id:
        try:
            nivel = NivelEducativo.objects.get(pk=nivel_id, activo=1)
        except NivelEducativo.DoesNotExist:
            nivel = None

    DocenteInstitucion.objects.update_or_create(
        docente=docente, institucion=institucion,
        defaults={'email_institucional': email_inst, 'nivel_educativo': nivel},
    )
    messages.success(request, f'{institucion.nombre} vinculada al docente.')
    return redirect('docentes_detalle', pk=pk)


@permiso_required('docentes.editar')
def institucion_actualizar(request, pk, vinc_pk):
    """Actualiza email institucional y nivel educativo de un vínculo existente."""
    vinc = get_object_or_404(DocenteInstitucion, pk=vinc_pk, docente_id=pk)
    if request.method != 'POST':
        return redirect('docentes_detalle', pk=pk)

    vinc.email_institucional = (request.POST.get('email_institucional') or '').strip() or None
    nivel_id = request.POST.get('nivel_educativo_id') or None
    vinc.nivel_educativo = None
    if nivel_id:
        try:
            vinc.nivel_educativo = NivelEducativo.objects.get(pk=nivel_id, activo=1)
        except NivelEducativo.DoesNotExist:
            pass
    vinc.save()
    messages.success(request, 'Vínculo actualizado.')
    return redirect('docentes_detalle', pk=pk)


@permiso_required('docentes.editar')
def institucion_desvincular(request, pk, vinc_pk):
    if request.method == 'POST':
        DocenteInstitucion.objects.filter(pk=vinc_pk, docente_id=pk).delete()
        messages.success(request, 'Institución desvinculada.')
    return redirect('docentes_detalle', pk=pk)


@permiso_required('usuarios.desactivar')
def desactivar(request, pk):
    docente = get_object_or_404(Docente.objects.select_related('usuario'), pk=pk)
    if request.method == 'POST':
        docente.usuario.activo = 0
        docente.usuario.save()
        messages.success(request, f'Docente {docente.usuario.nombre_completo} desactivado.')
    next_url = request.POST.get('next') or 'docentes_lista'
    if next_url == 'detalle':
        return redirect('docentes_detalle', pk=pk)
    return redirect('docentes_lista')


@permiso_required('usuarios.desactivar')
def activar(request, pk):
    docente = get_object_or_404(Docente.objects.select_related('usuario'), pk=pk)
    if request.method == 'POST':
        docente.usuario.activo = 1
        docente.usuario.save()
        messages.success(request, f'Docente {docente.usuario.nombre_completo} activado.')
    next_url = request.POST.get('next')
    if next_url == 'detalle':
        return redirect('docentes_detalle', pk=pk)
    return redirect('docentes_lista')


@permiso_required('docentes.editar')
def reset_password(request, pk):
    """Resetea la contraseña del docente con el mismo esquema que la creación:
    setea una nueva contraseña y marca must_change_password según el checkbox."""
    docente = get_object_or_404(Docente.objects.select_related('usuario'), pk=pk)
    if request.method != 'POST':
        return redirect('docentes_detalle', pk=pk)

    nueva = (request.POST.get('password') or '').strip()
    forzar = request.POST.get('forzar_cambio_password') == 'on'

    if len(nueva) < 6:
        messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
        return redirect('docentes_detalle', pk=pk)

    docente.usuario.password = hash_password(nueva)
    docente.usuario.must_change_password = 1 if forzar else 0
    docente.usuario.save()
    messages.success(request, f'Contraseña de {docente.usuario.nombre_completo} restablecida.')
    return redirect('docentes_detalle', pk=pk)