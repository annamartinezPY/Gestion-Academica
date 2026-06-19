"""Módulo del docente: gestión de sus cohortes con planilla, unidades y contenidos."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q

from ..decorators import login_required, get_usuario_sesion
from ..models import Cohorte, Docente, Unidad, Material, Tarea


def _docente_actual(request):
    """Retorna el Docente logueado, o None si no aplica."""
    usuario = get_usuario_sesion(request)
    if usuario['rol'] != 'docente' or not usuario.get('perfil_id'):
        return None, usuario
    try:
        return Docente.objects.get(pk=usuario['perfil_id']), usuario
    except Docente.DoesNotExist:
        return None, usuario


def _cohorte_del_docente(docente, cohorte_id):
    """Verifica que la cohorte pertenezca al docente (titular o sesiones)."""
    cohorte = get_object_or_404(
        Cohorte.objects.select_related('curso__modalidad', 'curso__institucion'),
        pk=cohorte_id,
    )
    cohortes_titular = Cohorte.objects.filter(docente=docente).values_list('id', flat=True)
    cohortes_sesiones = docente.sesiones.values_list('cohorte_id', flat=True)
    permitidas = set(cohortes_titular) | set(cohortes_sesiones)
    if cohorte.id not in permitidas:
        return None
    return cohorte


@login_required
def lista(request):
    """Página de tarjetas con las cohortes del docente."""
    docente, usuario = _docente_actual(request)
    if not docente:
        messages.error(request, 'Esta sección es exclusiva para docentes.')
        return redirect('dashboard')

    cohortes_titular = Cohorte.objects.filter(docente=docente).values_list('id', flat=True)
    cohortes_sesiones = docente.sesiones.values_list('cohorte_id', flat=True)
    permitidas = set(cohortes_titular) | set(cohortes_sesiones)

    cohortes = (Cohorte.objects
                .filter(id__in=permitidas)
                .select_related('curso__modalidad', 'curso__institucion')
                .annotate(
                    total_inscriptos=Count(
                        'inscripciones',
                        filter=Q(inscripciones__estado='activa'),
                        distinct=True,
                    ),
                    total_unidades=Count('unidades', filter=Q(unidades__activo=1), distinct=True),
                    total_materiales=Count('materiales', filter=Q(materiales__activo=1), distinct=True),
                    total_tareas=Count('tareas', filter=Q(tareas__activo=1), distinct=True),
                )
                .order_by('-fecha_inicio'))

    return render(request, 'mis_cohortes/lista.html', {
        'cohortes': cohortes,
        'usuario': usuario,
    })


@login_required
def detalle(request, cohorte_id):
    """Pantalla de gestión de una cohorte (tabs: planilla / unidades / contenidos)."""
    docente, usuario = _docente_actual(request)
    if not docente:
        return redirect('dashboard')

    cohorte = _cohorte_del_docente(docente, cohorte_id)
    if not cohorte:
        messages.error(request, 'No tenés acceso a esa cohorte.')
        return redirect('mis_cohortes_lista')

    unidades = list(cohorte.unidades.filter(activo=1).order_by('orden', 'id'))
    materiales = list(cohorte.materiales
                      .filter(activo=1)
                      .select_related('unidad', 'docente__usuario')
                      .order_by('unidad__orden', '-id'))
    tareas = list(cohorte.tareas
                  .filter(activo=1)
                  .select_related('unidad')
                  .order_by('unidad__orden', '-id'))

    # Agrupar materiales y tareas por unidad
    contenidos_por_unidad = {None: {'materiales': [], 'tareas': []}}
    for u in unidades:
        contenidos_por_unidad[u.id] = {'unidad': u, 'materiales': [], 'tareas': []}
    for m in materiales:
        contenidos_por_unidad.setdefault(m.unidad_id, {'unidad': None, 'materiales': [], 'tareas': []})
        contenidos_por_unidad[m.unidad_id]['materiales'].append(m)
    for t in tareas:
        contenidos_por_unidad.setdefault(t.unidad_id, {'unidad': None, 'materiales': [], 'tareas': []})
        contenidos_por_unidad[t.unidad_id]['tareas'].append(t)

    tab = request.GET.get('tab', 'planilla')
    if tab not in ('planilla', 'unidades', 'contenidos'):
        tab = 'planilla'

    return render(request, 'mis_cohortes/detalle.html', {
        'cohorte': cohorte,
        'unidades': unidades,
        'contenidos_por_unidad': contenidos_por_unidad,
        'tab_activo': tab,
        'usuario': usuario,
    })


# ── Planilla de cátedra ─────────────────────────────────────────────────

PLANILLA_MAX_PALABRAS = 1000
PLANILLA_PDF_MAX_MB = 10


@login_required
def planilla_guardar(request, cohorte_id):
    docente, _ = _docente_actual(request)
    if not docente:
        return redirect('dashboard')
    cohorte = _cohorte_del_docente(docente, cohorte_id)
    if not cohorte:
        return redirect('mis_cohortes_lista')

    if request.method == 'POST':
        texto = (request.POST.get('planilla_catedra') or '').strip()
        pdf = request.FILES.get('planilla_pdf')
        eliminar_pdf = request.POST.get('eliminar_pdf') == 'on'

        # ── Validar máximo 1000 palabras ──────────────────────────────────
        if texto:
            palabras = len(texto.split())
            if palabras > PLANILLA_MAX_PALABRAS:
                messages.error(
                    request,
                    f'La planilla supera el máximo permitido ({palabras} palabras, '
                    f'máx. {PLANILLA_MAX_PALABRAS}). Acortala antes de guardar.'
                )
                return redirect(f"/mis-cohortes/{cohorte.id}/?tab=planilla")

        # ── Validar PDF si lo subió ───────────────────────────────────────
        if pdf:
            nombre = (pdf.name or '').lower()
            if not nombre.endswith('.pdf'):
                messages.error(request, 'El archivo adjunto debe ser un PDF.')
                return redirect(f"/mis-cohortes/{cohorte.id}/?tab=planilla")
            if pdf.size > PLANILLA_PDF_MAX_MB * 1024 * 1024:
                messages.error(request, f'El PDF no debe superar los {PLANILLA_PDF_MAX_MB} MB.')
                return redirect(f"/mis-cohortes/{cohorte.id}/?tab=planilla")

        # ── Guardar ───────────────────────────────────────────────────────
        cohorte.planilla_catedra = texto or None
        if pdf:
            cohorte.planilla_pdf = pdf
        elif eliminar_pdf and cohorte.planilla_pdf:
            cohorte.planilla_pdf.delete(save=False)
            cohorte.planilla_pdf = None
        cohorte.save()
        messages.success(request, 'Planilla de cátedra guardada.')

    return redirect(f"/mis-cohortes/{cohorte.id}/?tab=planilla")


# ── Unidades ────────────────────────────────────────────────────────────

@login_required
def unidad_crear(request, cohorte_id):
    docente, _ = _docente_actual(request)
    if not docente:
        return redirect('dashboard')
    cohorte = _cohorte_del_docente(docente, cohorte_id)
    if not cohorte:
        return redirect('mis_cohortes_lista')

    if request.method == 'POST':
        titulo = (request.POST.get('titulo') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        if not titulo:
            messages.error(request, 'El título de la unidad es obligatorio.')
        else:
            # orden incremental
            ultimo = cohorte.unidades.order_by('-orden').first()
            siguiente_orden = (ultimo.orden + 1) if ultimo else 1
            Unidad.objects.create(
                cohorte=cohorte,
                titulo=titulo,
                descripcion=descripcion or None,
                orden=siguiente_orden,
                activo=1,
            )
            messages.success(request, f'Unidad "{titulo}" creada.')
    return redirect(f"/mis-cohortes/{cohorte.id}/?tab=unidades")


@login_required
def unidad_editar(request, cohorte_id, unidad_id):
    docente, _ = _docente_actual(request)
    if not docente:
        return redirect('dashboard')
    cohorte = _cohorte_del_docente(docente, cohorte_id)
    if not cohorte:
        return redirect('mis_cohortes_lista')

    unidad = get_object_or_404(Unidad, pk=unidad_id, cohorte=cohorte)
    if request.method == 'POST':
        titulo = (request.POST.get('titulo') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        if not titulo:
            messages.error(request, 'El título es obligatorio.')
        else:
            unidad.titulo = titulo
            unidad.descripcion = descripcion or None
            unidad.save()
            messages.success(request, 'Unidad actualizada.')
    return redirect(f"/mis-cohortes/{cohorte.id}/?tab=unidades")


@login_required
def unidad_toggle_visible(request, cohorte_id, unidad_id):
    """Alterna la visibilidad de una unidad para los estudiantes."""
    docente, _ = _docente_actual(request)
    if not docente:
        return redirect('dashboard')
    cohorte = _cohorte_del_docente(docente, cohorte_id)
    if not cohorte:
        return redirect('mis_cohortes_lista')

    unidad = get_object_or_404(Unidad, pk=unidad_id, cohorte=cohorte)
    if request.method == 'POST':
        if unidad.visible_estudiante:
            unidad.visible_estudiante = 0
            unidad.save()
            messages.info(request, f'Unidad "{unidad.titulo}" oculta para los estudiantes.')
        else:
            unidad.visible_estudiante = 1
            unidad.save()
            messages.success(request, f'Unidad "{unidad.titulo}" visible para los estudiantes.')
    return redirect(f"/mis-cohortes/{cohorte.id}/?tab=unidades")


@login_required
def unidad_eliminar(request, cohorte_id, unidad_id):
    docente, _ = _docente_actual(request)
    if not docente:
        return redirect('dashboard')
    cohorte = _cohorte_del_docente(docente, cohorte_id)
    if not cohorte:
        return redirect('mis_cohortes_lista')

    unidad = get_object_or_404(Unidad, pk=unidad_id, cohorte=cohorte)
    if request.method == 'POST':
        # Desvincular materiales/tareas en lugar de borrarlos
        Material.objects.filter(unidad=unidad).update(unidad=None)
        Tarea.objects.filter(unidad=unidad).update(unidad=None)
        unidad.activo = 0
        unidad.save()
        messages.success(request, f'Unidad "{unidad.titulo}" eliminada.')
    return redirect(f"/mis-cohortes/{cohorte.id}/?tab=unidades")


# ── Contenidos: materiales y tareas con FK a unidad ─────────────────────

@login_required
def material_crear(request, cohorte_id):
    docente, _ = _docente_actual(request)
    if not docente:
        return redirect('dashboard')
    cohorte = _cohorte_del_docente(docente, cohorte_id)
    if not cohorte:
        return redirect('mis_cohortes_lista')

    if request.method == 'POST':
        titulo = (request.POST.get('titulo') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        url_externa = (request.POST.get('url_externa') or '').strip()
        archivo = request.FILES.get('archivo')
        unidad_id = request.POST.get('unidad_id') or None

        if not titulo:
            messages.error(request, 'El título del material es obligatorio.')
        elif not archivo and not url_externa:
            messages.error(request, 'Debés adjuntar un archivo o ingresar una URL.')
        else:
            from datetime import date
            Material.objects.create(
                cohorte=cohorte,
                docente=docente,
                unidad_id=unidad_id if unidad_id else None,
                titulo=titulo,
                descripcion=descripcion or None,
                archivo=archivo or None,
                url_externa=url_externa or None,
                fecha_publicacion=date.today().isoformat(),
                activo=1,
            )
            messages.success(request, f'Material "{titulo}" publicado.')
    return redirect(f"/mis-cohortes/{cohorte.id}/?tab=contenidos")


@login_required
def material_eliminar(request, cohorte_id, material_id):
    docente, _ = _docente_actual(request)
    if not docente:
        return redirect('dashboard')
    cohorte = _cohorte_del_docente(docente, cohorte_id)
    if not cohorte:
        return redirect('mis_cohortes_lista')

    mat = get_object_or_404(Material, pk=material_id, cohorte=cohorte)
    if request.method == 'POST':
        mat.activo = 0
        mat.save()
        messages.success(request, 'Material eliminado.')
    return redirect(f"/mis-cohortes/{cohorte.id}/?tab=contenidos")


@login_required
def tarea_crear(request, cohorte_id):
    docente, _ = _docente_actual(request)
    if not docente:
        return redirect('dashboard')
    cohorte = _cohorte_del_docente(docente, cohorte_id)
    if not cohorte:
        return redirect('mis_cohortes_lista')

    if request.method == 'POST':
        titulo = (request.POST.get('titulo') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        fecha_entrega = (request.POST.get('fecha_entrega') or '').strip()
        puntos_raw = (request.POST.get('puntos_maximos') or '100').strip()
        archivo = request.FILES.get('archivo_consigna')
        unidad_id = request.POST.get('unidad_id') or None

        try:
            puntos = int(puntos_raw)
            if puntos < 0:
                raise ValueError
        except ValueError:
            puntos = 100

        if not titulo:
            messages.error(request, 'El título de la tarea es obligatorio.')
        else:
            from datetime import date
            Tarea.objects.create(
                cohorte=cohorte,
                docente=docente,
                unidad_id=unidad_id if unidad_id else None,
                titulo=titulo,
                descripcion=descripcion or None,
                archivo_consigna=archivo or None,
                fecha_entrega=fecha_entrega or None,
                puntos_maximos=puntos,
                fecha_creacion=date.today().isoformat(),
                activo=1,
            )
            messages.success(request, f'Tarea "{titulo}" creada.')
    return redirect(f"/mis-cohortes/{cohorte.id}/?tab=contenidos")


@login_required
def tarea_eliminar(request, cohorte_id, tarea_id):
    docente, _ = _docente_actual(request)
    if not docente:
        return redirect('dashboard')
    cohorte = _cohorte_del_docente(docente, cohorte_id)
    if not cohorte:
        return redirect('mis_cohortes_lista')

    tarea = get_object_or_404(Tarea, pk=tarea_id, cohorte=cohorte)
    if request.method == 'POST':
        tarea.activo = 0
        tarea.save()
        messages.success(request, 'Tarea eliminada.')
    return redirect(f"/mis-cohortes/{cohorte.id}/?tab=contenidos")
