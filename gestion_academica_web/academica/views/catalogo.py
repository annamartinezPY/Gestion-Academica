from django.shortcuts import render
from django.db.models import Q

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

    # --- Cargar docentes únicos por cohorte (1 query) ---
    cohorte_ids = [c.id for c in cohortes]
    docentes_por_cohorte = {cid: [] for cid in cohorte_ids}
    if cohorte_ids:
        sesiones = (Sesion.objects
                    .filter(cohorte_id__in=cohorte_ids)
                    .select_related('docente__usuario')
                    .order_by('docente__usuario__apellido'))
        vistos = {cid: set() for cid in cohorte_ids}
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

    return render(request, 'catalogo/index.html', {
        'usuario': usuario,
        'cohortes': cohortes,
        'modalidades': modalidades,
        'instituciones': instituciones,
        'inscriptos_ids': inscriptos_ids,
        'total': len(cohortes),
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
