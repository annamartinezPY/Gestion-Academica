"""Portal del estudiante: Mis Cursos (cohortes en curso).

Vista de tarjetas + aula virtual (split-screen con accordion de unidades
y workspace dinámico por material o tarea seleccionada).
"""
from datetime import date, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q

from ..decorators import login_required, get_usuario_sesion
from ..models import (
    Estudiante, Inscripcion, Cohorte,
    Unidad, Material, Tarea, EntregaTarea, Docente,
)


def _estudiante_actual(request):
    """Retorna el Estudiante logueado, o None si no aplica."""
    usuario = get_usuario_sesion(request)
    if usuario['rol'] != 'estudiante' or not usuario.get('perfil_id'):
        return None, usuario
    try:
        return Estudiante.objects.select_related('usuario').get(pk=usuario['perfil_id']), usuario
    except Estudiante.DoesNotExist:
        return None, usuario


def _docente_titular_o_principal(cohorte):
    """Devuelve el docente titular de la cohorte, o el primero que dictó una sesión."""
    if cohorte.docente_id:
        return cohorte.docente
    primera = cohorte.sesiones.select_related('docente__usuario').first()
    return primera.docente if primera else None


@login_required
def lista(request):
    """Grilla de tarjetas con las cohortes activas del estudiante."""
    estudiante, usuario = _estudiante_actual(request)
    if not estudiante:
        messages.error(request, 'Esta sección es exclusiva para estudiantes.')
        return redirect('dashboard')

    inscripciones = (Inscripcion.objects
                     .filter(estudiante=estudiante, estado='activa')
                     .select_related(
                         'cohorte__curso__modalidad',
                         'cohorte__curso__institucion',
                         'cohorte__docente__usuario',
                     )
                     .order_by('-fecha_inscripcion'))

    cohorte_ids = [i.cohorte_id for i in inscripciones]
    cohortes = (Cohorte.objects
                .filter(id__in=cohorte_ids)
                .annotate(
                    total_unidades=Count('unidades', filter=Q(unidades__activo=1), distinct=True),
                    total_materiales=Count('materiales', filter=Q(materiales__activo=1), distinct=True),
                    total_tareas=Count('tareas', filter=Q(tareas__activo=1), distinct=True),
                ))
    cohortes_map = {c.id: c for c in cohortes}

    # Calcular progreso: % = tareas_entregadas / total_tareas
    entregas_por_cohorte = {}
    for entrega in EntregaTarea.objects.filter(
        estudiante=estudiante,
        tarea__cohorte_id__in=cohorte_ids,
        tarea__activo=1,
    ).select_related('tarea__cohorte'):
        cid = entrega.tarea.cohorte_id
        entregas_por_cohorte[cid] = entregas_por_cohorte.get(cid, 0) + 1

    # Armar cards
    hoy = date.today()
    cards = []
    for ins in inscripciones:
        c = cohortes_map.get(ins.cohorte_id)
        if not c:
            continue
        total_tar = c.total_tareas or 0
        entregadas = entregas_por_cohorte.get(c.id, 0)
        progreso = int((entregadas * 100) / total_tar) if total_tar > 0 else 0

        # Tareas pendientes (sin entregar) que estén activas
        tareas_pendientes = 0
        tareas_cohorte = Tarea.objects.filter(cohorte=c, activo=1)
        entregadas_ids = set(EntregaTarea.objects.filter(
            estudiante=estudiante, tarea__in=tareas_cohorte,
        ).values_list('tarea_id', flat=True))
        for t in tareas_cohorte:
            if t.id not in entregadas_ids:
                tareas_pendientes += 1

        docente_principal = _docente_titular_o_principal(c)

        cards.append({
            'cohorte': c,
            'docente': docente_principal,
            'progreso': progreso,
            'tareas_pendientes': tareas_pendientes,
        })

    return render(request, 'mis_cursos/lista.html', {
        'usuario': usuario,
        'estudiante': estudiante,
        'cards': cards,
        'total_cursos': len(cards),
    })


def _cohorte_inscripto(estudiante, cohorte_id):
    """Verifica inscripción activa y devuelve la cohorte; None si no aplica."""
    cohorte = get_object_or_404(
        Cohorte.objects.select_related(
            'curso__modalidad', 'curso__institucion', 'docente__usuario'
        ),
        pk=cohorte_id,
    )
    inscripto = Inscripcion.objects.filter(
        estudiante=estudiante, cohorte=cohorte, estado='activa'
    ).exists()
    return cohorte if inscripto else None


@login_required
def aula(request, cohorte_id):
    """Pantalla split-screen: accordion de unidades a la izquierda + workspace a la derecha."""
    estudiante, usuario = _estudiante_actual(request)
    if not estudiante:
        return redirect('dashboard')

    cohorte = _cohorte_inscripto(estudiante, cohorte_id)
    if not cohorte:
        messages.error(request, 'No estás inscripto en este curso.')
        return redirect('mis_cursos_lista')

    # Cargar contenidos
    unidades = list(cohorte.unidades.filter(activo=1).order_by('orden', 'id'))
    materiales = list(cohorte.materiales
                      .filter(activo=1)
                      .select_related('unidad'))
    tareas = list(cohorte.tareas
                  .filter(activo=1)
                  .select_related('unidad'))

    # Mapa de entregas del estudiante (tarea_id -> EntregaTarea)
    entregas_map = {
        e.tarea_id: e for e in EntregaTarea.objects.filter(
            estudiante=estudiante, tarea__in=tareas,
        )
    }

    # Agrupar por unidad (None = sin unidad asignada)
    arbol = []
    for u in unidades:
        items = []
        for m in materiales:
            if m.unidad_id == u.id:
                items.append({'tipo': 'material', 'obj': m})
        for t in tareas:
            if t.unidad_id == u.id:
                items.append({'tipo': 'tarea', 'obj': t, 'entrega': entregas_map.get(t.id)})
        arbol.append({'unidad': u, 'items': items})

    # Sección "sin unidad"
    sin_unidad = []
    for m in materiales:
        if not m.unidad_id:
            sin_unidad.append({'tipo': 'material', 'obj': m})
    for t in tareas:
        if not t.unidad_id:
            sin_unidad.append({'tipo': 'tarea', 'obj': t, 'entrega': entregas_map.get(t.id)})
    if sin_unidad:
        arbol.append({'unidad': None, 'items': sin_unidad})

    # Item seleccionado en el workspace
    item_sel = request.GET.get('item') or ''
    item_actual = None  # dict con tipo, obj, entrega
    if item_sel.startswith('mat-'):
        try:
            mid = int(item_sel[4:])
            for m in materiales:
                if m.id == mid:
                    item_actual = {'tipo': 'material', 'obj': m}
                    break
        except ValueError:
            pass
    elif item_sel.startswith('tar-'):
        try:
            tid = int(item_sel[4:])
            for t in tareas:
                if t.id == tid:
                    item_actual = {'tipo': 'tarea', 'obj': t, 'entrega': entregas_map.get(t.id)}
                    break
        except ValueError:
            pass

    # KPIs para el header
    total_unidades = len(unidades)
    total_materiales = len(materiales)
    total_tareas = len(tareas)
    tareas_entregadas = sum(1 for t in tareas if t.id in entregas_map)
    progreso = int((tareas_entregadas * 100) / total_tareas) if total_tareas > 0 else 0
    docente_principal = _docente_titular_o_principal(cohorte)

    # Fecha de hoy en ISO para comparar con fecha_entrega
    hoy_iso = date.today().isoformat()

    return render(request, 'mis_cursos/aula.html', {
        'usuario': usuario,
        'estudiante': estudiante,
        'cohorte': cohorte,
        'docente_principal': docente_principal,
        'arbol': arbol,
        'item_actual': item_actual,
        'item_sel': item_sel,
        'kpis': {
            'unidades': total_unidades,
            'materiales': total_materiales,
            'tareas': total_tareas,
            'entregadas': tareas_entregadas,
            'progreso': progreso,
        },
        'hoy_iso': hoy_iso,
    })


@login_required
def entregar(request, cohorte_id, tarea_id):
    """POST: el estudiante entrega/actualiza una tarea desde el aula."""
    estudiante, _ = _estudiante_actual(request)
    if not estudiante:
        return redirect('dashboard')

    cohorte = _cohorte_inscripto(estudiante, cohorte_id)
    if not cohorte:
        return redirect('mis_cursos_lista')

    tarea = get_object_or_404(Tarea, pk=tarea_id, cohorte=cohorte, activo=1)
    entrega = EntregaTarea.objects.filter(tarea=tarea, estudiante=estudiante).first()

    if request.method != 'POST':
        return redirect(f"/mis-cursos/{cohorte.id}/aula/?item=tar-{tarea.id}")

    archivo = request.FILES.get('archivo')
    comentario = (request.POST.get('comentario') or '').strip() or None
    if not archivo and not (entrega and entrega.archivo):
        messages.error(request, 'Debés adjuntar un archivo para entregar.')
        return redirect(f"/mis-cursos/{cohorte.id}/aula/?item=tar-{tarea.id}")

    ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if entrega:
        if archivo:
            entrega.archivo = archivo
        entrega.comentario = comentario
        entrega.fecha_entrega = ahora
        entrega.save()
        messages.success(request, '✓ Entrega actualizada.')
    else:
        EntregaTarea.objects.create(
            tarea=tarea, estudiante=estudiante,
            archivo=archivo, comentario=comentario,
            fecha_entrega=ahora,
        )
        messages.success(request, '✓ Tarea entregada con éxito.')
    return redirect(f"/mis-cursos/{cohorte.id}/aula/?item=tar-{tarea.id}")
