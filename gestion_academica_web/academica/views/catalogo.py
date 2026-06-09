from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator

from ..decorators import login_required, get_usuario_sesion
from ..models import Cohorte, Modalidad, Institucion, Inscripcion, Sesion, Docente


@login_required
def catalogo(request):
    usuario = get_usuario_sesion(request)

    # --- Filtros desde GET ---
    q_texto     = request.GET.get('q', '').strip()
    modalidad_id = request.GET.get('modalidad', '')
    institucion_id = request.GET.get('institucion', '')
    fecha_desde  = request.GET.get('fecha_desde', '')
    fecha_hasta  = request.GET.get('fecha_hasta', '')
    solo_con_cupo = request.GET.get('con_cupo', '')

    # --- Base queryset: solo cohortes activas con curso activo ---
    cohortes = (Cohorte.objects
                .filter(activo=1, curso__activo=1)
                .select_related('curso__modalidad', 'curso__institucion')
                .order_by('fecha_inicio'))

    # --- Aplicar filtros ---
    if q_texto:
        cohortes = cohortes.filter(
            Q(curso__nombre__icontains=q_texto) |
            Q(nombre__icontains=q_texto) |
            Q(curso__descripcion__icontains=q_texto)
        )

    if modalidad_id:
        cohortes = cohortes.filter(curso__modalidad_id=modalidad_id)

    if institucion_id:
        cohortes = cohortes.filter(curso__institucion_id=institucion_id)

    if fecha_desde:
        cohortes = cohortes.filter(fecha_inicio__gte=fecha_desde)

    if fecha_hasta:
        cohortes = cohortes.filter(fecha_inicio__lte=fecha_hasta)

    # --- Filtro "con cupo disponible" se aplica en Python (usa propiedad) ---
    if solo_con_cupo:
        cohortes = [c for c in cohortes if c.cupo_disponible]
    else:
        cohortes = list(cohortes)

    # --- Cargar docentes únicos por cohorte (titular + de sesiones) ---
    cohorte_ids = [c.id for c in cohortes]
    docentes_por_cohorte = {cid: [] for cid in cohorte_ids}
    vistos = {cid: set() for cid in cohorte_ids}

    # 1) Docente titular asignado a la cohorte (si existe)
    titulares = (Cohorte.objects
                 .filter(id__in=cohorte_ids, docente__isnull=False)
                 .select_related('docente__usuario'))
    for coh in titulares:
        docentes_por_cohorte[coh.id].append(coh.docente)
        vistos[coh.id].add(coh.docente_id)

    # 2) Docentes que dictan sesiones (deduplicados)
    if cohorte_ids:
        sesiones = (Sesion.objects
                    .filter(cohorte_id__in=cohorte_ids)
                    .select_related('docente__usuario')
                    .order_by('docente__usuario__apellido'))
        for s in sesiones:
            if s.docente_id not in vistos[s.cohorte_id]:
                vistos[s.cohorte_id].add(s.docente_id)
                docentes_por_cohorte[s.cohorte_id].append(s.docente)

    for c in cohortes:
        c.docentes_lista = docentes_por_cohorte.get(c.id, [])

    # --- Opciones para los selects de filtro ---
    modalidades   = Modalidad.objects.all().order_by('nombre')
    instituciones = Institucion.objects.filter(activo=1).order_by('nombre')

    # --- Para el portal estudiante: saber en cuáles ya está inscripto ---
    inscriptos_ids = set()
    if usuario['rol'] == 'estudiante' and usuario.get('perfil_id'):
        inscriptos_ids = set(
            Inscripcion.objects.filter(
                estudiante_id=usuario['perfil_id'],
                estado='activa',
            ).values_list('cohorte_id', flat=True)
        )

    total = len(cohortes)
    paginator = Paginator(cohortes, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    qs_parts = []
    if q_texto: qs_parts.append(f'q={q_texto}')
    if modalidad_id: qs_parts.append(f'modalidad={modalidad_id}')
    if institucion_id: qs_parts.append(f'institucion={institucion_id}')
    if fecha_desde: qs_parts.append(f'fecha_desde={fecha_desde}')
    if fecha_hasta: qs_parts.append(f'fecha_hasta={fecha_hasta}')
    if solo_con_cupo: qs_parts.append(f'con_cupo={solo_con_cupo}')

    return render(request, 'catalogo/index.html', {
        'usuario': usuario,
        'cohortes': page_obj,
        'page_obj': page_obj,
        'querystring': '&'.join(qs_parts),
        'modalidades': modalidades,
        'instituciones': instituciones,
        'inscriptos_ids': inscriptos_ids,
        'total': total,
        # Para repopular los filtros
        'filtros': {
            'q': q_texto,
            'modalidad': modalidad_id,
            'institucion': institucion_id,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'con_cupo': solo_con_cupo,
        },
    })


@login_required
def cohorte_detalle(request, pk):
    """Vista pública (para estudiantes) del detalle de un curso/cohorte:
    días de clase, horarios y todos los docentes que lo dictan."""
    usuario = get_usuario_sesion(request)
    cohorte = get_object_or_404(
        Cohorte.objects
            .select_related('curso__modalidad', 'curso__institucion',
                            'docente__usuario', 'docente__nivel_educativo')
            .filter(activo=1, curso__activo=1),
        pk=pk,
    )

    # Docentes únicos en esta cohorte: titular asignado + los que dictan sesiones
    sesiones = (Sesion.objects
                .filter(cohorte_id=cohorte.id)
                .select_related('docente__usuario', 'docente__nivel_educativo')
                .order_by('fecha', 'hora_inicio'))
    vistos = set()
    docentes = []
    # 1) Titular de la cohorte (si existe)
    if cohorte.docente_id:
        docentes.append(cohorte.docente)
        vistos.add(cohorte.docente_id)
    # 2) Docentes que dictan sesiones (deduplicados)
    for s in sesiones:
        if s.docente_id not in vistos:
            vistos.add(s.docente_id)
            docentes.append(s.docente)

    # Próximas sesiones (las primeras 6 a partir de hoy, si existen)
    from datetime import date
    hoy = date.today().isoformat()
    proximas_sesiones = [s for s in sesiones if s.fecha and s.fecha >= hoy][:6]

    # ¿Ya inscripto?
    ya_inscripto = False
    if usuario['rol'] == 'estudiante' and usuario.get('perfil_id'):
        ya_inscripto = Inscripcion.objects.filter(
            estudiante_id=usuario['perfil_id'],
            cohorte_id=cohorte.id,
            estado='activa',
        ).exists()

    return render(request, 'catalogo/detail.html', {
        'usuario': usuario,
        'cohorte': cohorte,
        'docentes': docentes,
        'proximas_sesiones': proximas_sesiones,
        'total_sesiones': sesiones.count(),
        'ya_inscripto': ya_inscripto,
    })
