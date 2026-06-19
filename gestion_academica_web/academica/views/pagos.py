import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from ..decorators import permiso_required, get_usuario_sesion
from ..models import (
    PagoEstudiante, PagoDocente, Inscripcion,
    Docente, Cohorte, Estudiante, Usuario, Notificacion, Sesion,
)
from ..forms import PagoEstudianteForm


# ──────────────────────────────────────────────
#  Pagos de estudiantes
# ──────────────────────────────────────────────

@permiso_required('pagos.ver')
def lista_estudiantes(request):
    cohorte_id  = request.GET.get('cohorte')
    filtro_estado = request.GET.get('estado', '')
    qs = PagoEstudiante.objects.select_related(
        'inscripcion__estudiante__usuario',
        'inscripcion__cohorte__curso__institucion',
        'revisado_por',
    ).order_by('-fecha_pago')
    if cohorte_id:
        qs = qs.filter(inscripcion__cohorte_id=cohorte_id)
    if filtro_estado:
        qs = qs.filter(estado=filtro_estado)

    cohortes = Cohorte.objects.select_related('curso').order_by('-fecha_inicio')
    pendientes_count = PagoEstudiante.objects.filter(estado='pendiente').count()
    en_revision_count = PagoEstudiante.objects.filter(estado='en_revision').count()
    total = sum(p.monto for p in qs if p.estado == 'aprobado')

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    qs_parts = []
    if cohorte_id: qs_parts.append(f'cohorte={cohorte_id}')
    if filtro_estado: qs_parts.append(f'estado={filtro_estado}')

    return render(request, 'pagos/lista_estudiantes.html', {
        'pagos': page_obj,
        'page_obj': page_obj,
        'querystring': '&'.join(qs_parts),
        'cohortes': cohortes,
        'filtro_cohorte': cohorte_id,
        'filtro_estado': filtro_estado,
        'total': total,
        'pendientes_count': pendientes_count,
        'en_revision_count': en_revision_count,
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('pagos.crear')
def nuevo_pago_estudiante(request):
    cohorte_id = request.GET.get('cohorte') or request.POST.get('cohorte_id_sel')
    cohortes = Cohorte.objects.select_related('curso').order_by('-fecha_inicio')
    inscripciones = []
    cohorte_sel = None

    if cohorte_id:
        try:
            cohorte_sel = Cohorte.objects.select_related('curso').get(pk=cohorte_id)
            inscripciones = Inscripcion.objects.filter(
                cohorte_id=cohorte_id, estado='activa'
            ).select_related('estudiante__usuario')
        except Cohorte.DoesNotExist:
            pass

    if request.method == 'POST' and request.POST.get('inscripcion_id'):
        form = PagoEstudianteForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            PagoEstudiante.objects.create(
                inscripcion_id=d['inscripcion_id'],
                monto=d['monto'],
                metodo_pago=d['metodo_pago'],
                observacion=d.get('observacion') or '',
                fecha_pago=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                estado='pagado',
            )
            messages.success(request, f'Pago de ${d["monto"]:.2f} registrado.')
            return redirect('pagos_estudiantes')
    else:
        form = PagoEstudianteForm()

    return render(request, 'pagos/form_estudiante.html', {
        'form': form, 'cohortes': cohortes,
        'cohorte_sel': cohorte_sel, 'inscripciones': inscripciones,
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('pagos.anular')
def anular_pago_estudiante(request, pk):
    pago = get_object_or_404(PagoEstudiante, pk=pk)
    if request.method == 'POST':
        if pago.estado != 'anulado':
            pago.estado = 'anulado'
            pago.save()
            messages.success(request, 'Pago anulado.')
        else:
            messages.warning(request, 'El pago ya está anulado.')
    return redirect('pagos_estudiantes')


@permiso_required('pagos.aprobar')
def poner_en_revision(request, pk):
    """Marca un pago pendiente como EN REVISIÓN."""
    pago = get_object_or_404(PagoEstudiante, pk=pk)
    if request.method == 'POST' and pago.estado == PagoEstudiante.ESTADO_PENDIENTE:
        pago.estado = PagoEstudiante.ESTADO_EN_REVISION
        pago.save()
        messages.success(request, 'Pago marcado como En Revisión.')
    return redirect('pagos_estudiantes')


@permiso_required('pagos.aprobar')
def aprobar_pago(request, pk):
    """Aprueba un pago en revisión, asigna número de recibo."""
    pago = get_object_or_404(PagoEstudiante, pk=pk)
    if request.method == 'POST' and pago.estado in (
        PagoEstudiante.ESTADO_PENDIENTE, PagoEstudiante.ESTADO_EN_REVISION
    ):
        numero_recibo = request.POST.get('numero_recibo', '').strip()
        usuario_id = request.session.get('usuario_id')
        pago.estado = PagoEstudiante.ESTADO_APROBADO
        pago.numero_recibo = numero_recibo or None
        pago.fecha_revision = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if usuario_id:
            try:
                pago.revisado_por = Usuario.objects.get(pk=usuario_id)
            except Usuario.DoesNotExist:
                pass
        pago.motivo_rechazo = None
        pago.save()
        # Notificar al estudiante
        est_usuario_id = pago.inscripcion.estudiante.usuario_id
        Notificacion.notificar(
            usuario_id=est_usuario_id,
            titulo='Pago verificado',
            mensaje=f'Tu pago de Gs. {int(pago.monto):,} fue verificado por Tesorería.',
            tipo='success',
            url='/mis-pagos/',
        )
        messages.success(request, f'Pago aprobado correctamente.')
    return redirect('pagos_estudiantes')


@permiso_required('pagos.aprobar')
def rechazar_pago(request, pk):
    """Rechaza un pago indicando el motivo."""
    pago = get_object_or_404(PagoEstudiante, pk=pk)
    if request.method == 'POST' and pago.estado in (
        PagoEstudiante.ESTADO_PENDIENTE, PagoEstudiante.ESTADO_EN_REVISION
    ):
        motivo = request.POST.get('motivo_rechazo', '').strip()
        usuario_id = request.session.get('usuario_id')
        pago.estado = PagoEstudiante.ESTADO_RECHAZADO
        pago.motivo_rechazo = motivo or 'Sin motivo especificado.'
        pago.fecha_revision = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if usuario_id:
            try:
                pago.revisado_por = Usuario.objects.get(pk=usuario_id)
            except Usuario.DoesNotExist:
                pass
        pago.save()
        est_usuario_id = pago.inscripcion.estudiante.usuario_id
        Notificacion.notificar(
            usuario_id=est_usuario_id,
            titulo='Pago rechazado',
            mensaje=f'Tu pago de Gs. {int(pago.monto):,} fue rechazado. Motivo: {pago.motivo_rechazo}',
            tipo='danger',
            url='/mis-pagos/',
        )
        messages.warning(request, f'Pago rechazado.')
    return redirect('pagos_estudiantes')


# ──────────────────────────────────────────────
#  Pagos a docentes
# ──────────────────────────────────────────────

@permiso_required('pagos.ver')
def lista_docentes(request):
    """Dashboard de PRE-LIQUIDACIÓN: calcula automáticamente el saldo pendiente
    de cada docente por cohorte, basado en sesiones verificadas × tarifa, y muestra
    el capital disponible (cobrado a estudiantes menos ya pagado a docentes).

    El tesorero ve qué se le debe a cada docente y cuánto capital hay disponible
    en cada cohorte para hacer frente al pago.
    """
    docentes = (Docente.objects
                .select_related('usuario')
                .filter(usuario__activo=1))
    docentes_para_select = list(docentes.order_by('usuario__apellido', 'usuario__nombre'))

    cohortes = (Cohorte.objects
                .filter(activo=1)
                .select_related('curso__institucion', 'curso__modalidad'))
    cohortes_para_select = list(cohortes.order_by('-fecha_inicio'))

    # ── Por cohorte: capital recibido (estudiantes) y distribuido (docentes) ──
    capital_por_cohorte = {}
    for c in cohortes:
        cap_recibido = (PagoEstudiante.objects
                        .filter(inscripcion__cohorte=c,
                                estado__in=['aprobado', 'pagado'])
                        .aggregate(t=Sum('monto'))['t'] or 0)
        cap_distribuido = (PagoDocente.objects
                           .filter(cohorte=c, estado='pagado')
                           .aggregate(t=Sum('monto'))['t'] or 0)
        inscriptos = Inscripcion.objects.filter(cohorte=c, estado='activa').count()
        capital_por_cohorte[c.id] = {
            'cohorte': c,
            'capital_recibido': cap_recibido,
            'capital_distribuido': cap_distribuido,
            'capital_disponible': max(0, cap_recibido - cap_distribuido),
            'inscriptos': inscriptos,
        }

    # ── Helpers de cálculo de horas ──────────────────────────────────────
    from datetime import datetime as _dt, date as _date, timedelta as _td

    DIAS_MAP = {
        'lunes': 0, 'martes': 1, 'miércoles': 2, 'miercoles': 2,
        'jueves': 3, 'viernes': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6,
    }

    def _horas_sesion_planificadas(s):
        """Horas planificadas de una Sesion usando hora_inicio y hora_fin."""
        try:
            t1 = _dt.strptime(str(s.hora_inicio)[:5], '%H:%M')
            t2 = _dt.strptime(str(s.hora_fin)[:5], '%H:%M')
            delta = (t2 - t1).total_seconds() / 3600
            return round(delta, 2) if delta > 0 else 0
        except Exception:
            return 0

    def _horas_cronograma_cohorte(cohorte, hasta=None):
        """Calcula horas planificadas de la cohorte según su CRONOGRAMA.
        Retorna (clases_totales, horas_totales, clases_a_la_fecha, horas_a_la_fecha).
        - Total: fecha_inicio a fecha_fin (proyección completa)
        - A la fecha: fecha_inicio a mín(fecha_fin, hoy) — lo ya devengado
        """
        if not cohorte.dias_clase or not cohorte.carga_horaria_diaria:
            return 0, 0, 0, 0
        dias = set()
        for token in cohorte.dias_clase.split(','):
            t = token.strip().lower()
            if t in DIAS_MAP:
                dias.add(DIAS_MAP[t])
        if not dias:
            return 0, 0, 0, 0
        try:
            fi = _date.fromisoformat(str(cohorte.fecha_inicio)[:10])
            ff = _date.fromisoformat(str(cohorte.fecha_fin)[:10])
        except (ValueError, TypeError):
            return 0, 0, 0, 0
        if hasta is None:
            hasta = _date.today()
        carga = cohorte.carga_horaria_diaria or 0

        # Total planificado (todo el período)
        clases_total = 0
        cur = fi
        while cur <= ff:
            if cur.weekday() in dias:
                clases_total += 1
            cur += _td(days=1)
        horas_total = clases_total * carga

        # A la fecha (hasta hoy clamp con fecha_fin)
        limite = min(ff, hasta)
        clases_hoy = 0
        if fi <= limite:
            cur = fi
            while cur <= limite:
                if cur.weekday() in dias:
                    clases_hoy += 1
                cur += _td(days=1)
        horas_hoy = clases_hoy * carga

        return clases_total, round(horas_total, 2), clases_hoy, round(horas_hoy, 2)

    # ── Por docente × cohorte: monto devengado, ya pagado y saldo ──
    filas = []
    for d in docentes:
        # Cohortes donde es titular o donde dictó sesiones
        cohortes_titular = set(Cohorte.objects.filter(docente=d, activo=1).values_list('id', flat=True))
        cohortes_sesiones = set(d.sesiones.values_list('cohorte_id', flat=True))
        cohortes_ids = cohortes_titular | cohortes_sesiones

        for cid in cohortes_ids:
            info_c = capital_por_cohorte.get(cid)
            if not info_c:
                continue
            cohorte = info_c['cohorte']
            es_titular = cid in cohortes_titular

            # Estrategia híbrida:
            # - Si el docente es TITULAR: usamos el cronograma planificado completo
            #   (devengado = TOTAL del cronograma; se muestra también lo dictado a la fecha)
            # - Si NO es titular: sumamos sólo las sesiones que dictó individualmente
            if es_titular:
                clases_tot, horas_tot, clases_hoy, horas_hoy = _horas_cronograma_cohorte(cohorte)
                horas_total = horas_tot
                clases_calc = clases_tot
                origen_calculo = 'cronograma'
            else:
                sesiones_dictadas = (Sesion.objects
                                     .filter(docente=d, cohorte=cohorte)
                                     .exclude(estado='cancelada'))
                horas_total = sum(_horas_sesion_planificadas(s) for s in sesiones_dictadas)
                clases_calc = sesiones_dictadas.count()
                horas_hoy = horas_total
                clases_hoy = clases_calc
                origen_calculo = 'sesiones'

            monto_devengado = round(horas_total * (d.tarifa_hora or 0), 2)

            # Ya pagado a este docente en esta cohorte
            ya_pagado = (PagoDocente.objects
                         .filter(docente=d, cohorte=cohorte, estado='pagado')
                         .aggregate(t=Sum('monto'))['t'] or 0)

            saldo_pendiente = max(0, monto_devengado - ya_pagado)

            # Mostramos filas con actividad o saldo pendiente
            if horas_total <= 0 and saldo_pendiente <= 0:
                continue

            filas.append({
                'docente': d,
                'cohorte': cohorte,
                'institucion': cohorte.curso.institucion,
                'inscriptos': info_c['inscriptos'],
                'sesiones_dictadas': clases_calc,
                'horas_dictadas': round(horas_total, 2),
                'horas_a_la_fecha': horas_hoy,
                'clases_a_la_fecha': clases_hoy,
                'tarifa_hora': d.tarifa_hora or 0,
                'monto_devengado': monto_devengado,
                'ya_pagado': ya_pagado,
                'saldo_pendiente': saldo_pendiente,
                'capital_recibido': info_c['capital_recibido'],
                'capital_disponible': info_c['capital_disponible'],
                'origen_calculo': origen_calculo,
                'es_titular': es_titular,
            })

    filas.sort(key=lambda r: -r['saldo_pendiente'])

    # ── KPIs globales ──
    total_devengado = sum(f['monto_devengado'] for f in filas)
    total_pendiente = sum(f['saldo_pendiente'] for f in filas)
    total_capital_recibido = sum(info['capital_recibido'] for info in capital_por_cohorte.values())
    total_capital_distribuido = sum(info['capital_distribuido'] for info in capital_por_cohorte.values())
    total_capital_disponible = max(0, total_capital_recibido - total_capital_distribuido)

    # Historial reciente de liquidaciones (últimas 10)
    historial_reciente = (PagoDocente.objects
                          .filter(estado='pagado')
                          .select_related('docente__usuario', 'cohorte__curso', 'institucion')
                          .order_by('-fecha_pago')[:10])

    return render(request, 'pagos/lista_docentes.html', {
        'filas': filas,
        'historial_reciente': historial_reciente,
        'docentes_select': docentes_para_select,
        'cohortes_select': cohortes_para_select,
        'kpis': {
            'total_devengado': total_devengado,
            'total_pendiente': total_pendiente,
            'capital_recibido': total_capital_recibido,
            'capital_distribuido': total_capital_distribuido,
            'capital_disponible': total_capital_disponible,
        },
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('pagos.crear')
def liquidar_pago_directo(request):
    """Crea Y paga un PagoDocente atómicamente desde el dashboard de pre-liquidación.
    El monto, docente, cohorte vienen pre-calculados por el sistema."""
    if request.method != 'POST':
        return redirect('pagos_docentes')

    docente_id = request.POST.get('docente_id')
    cohorte_id = request.POST.get('cohorte_id')
    monto_raw  = (request.POST.get('monto') or '').strip()
    metodo     = (request.POST.get('metodo_pago') or '').strip()
    observacion = (request.POST.get('observacion') or '').strip() or None
    comprobante = request.FILES.get('comprobante')

    try:
        docente = Docente.objects.select_related('usuario').get(pk=docente_id)
        cohorte = Cohorte.objects.select_related('curso__institucion').get(pk=cohorte_id)
    except (Docente.DoesNotExist, Cohorte.DoesNotExist):
        messages.error(request, 'Docente o cohorte no encontrado.')
        return redirect('pagos_docentes')

    # Validar monto
    try:
        monto = float(monto_raw.replace('.', '').replace(',', ''))
        if monto <= 0:
            raise ValueError
    except ValueError:
        messages.error(request, 'El monto debe ser un número mayor a cero.')
        return redirect('pagos_docentes')

    # Validar método y comprobante
    if metodo not in ('transferencia', 'cheque', 'efectivo'):
        messages.error(request, 'Seleccioná un método de pago válido.')
        return redirect('pagos_docentes')

    if metodo in ('transferencia', 'cheque') and not comprobante:
        messages.error(request, f'Adjuntá el comprobante del {metodo}.')
        return redirect('pagos_docentes')

    if comprobante:
        ext = (comprobante.name.rsplit('.', 1)[-1] or '').lower()
        if ext not in ('pdf', 'jpg', 'jpeg', 'png'):
            messages.error(request, 'El comprobante debe ser PDF, JPG o PNG.')
            return redirect('pagos_docentes')
        if comprobante.size > 5 * 1024 * 1024:
            messages.error(request, 'El comprobante no debe superar 5 MB.')
            return redirect('pagos_docentes')

    # Validar capital disponible de la cohorte (no se puede pagar más
    # de lo cobrado a los estudiantes ‒ ya distribuido a otros docentes).
    cap_recibido = (PagoEstudiante.objects
                    .filter(inscripcion__cohorte=cohorte,
                            estado__in=['aprobado', 'pagado'])
                    .aggregate(t=Sum('monto'))['t'] or 0)
    cap_distribuido = (PagoDocente.objects
                       .filter(cohorte=cohorte, estado='pagado')
                       .aggregate(t=Sum('monto'))['t'] or 0)
    capital_disponible = max(0, float(cap_recibido) - float(cap_distribuido))

    if capital_disponible <= 0:
        messages.error(
            request,
            f'No hay capital disponible en la cohorte «{cohorte.nombre}». '
            f'Recibido: ₲ {int(cap_recibido):,} · Distribuido: ₲ {int(cap_distribuido):,}.'
            .replace(',', '.')
        )
        return redirect('pagos_docentes')

    if monto > capital_disponible:
        messages.error(
            request,
            f'Capital insuficiente: el monto ₲ {int(monto):,} supera el capital '
            f'disponible (₲ {int(capital_disponible):,}) en la cohorte «{cohorte.nombre}». '
            f'Esperá a que ingresen más pagos de estudiantes o pagá un monto parcial.'
            .replace(',', '.')
        )
        return redirect('pagos_docentes')

    # Calcular horas dictadas (planificadas, sin cancelar)
    def _hr_plan(s):
        try:
            from datetime import datetime
            t1 = datetime.strptime(str(s.hora_inicio)[:5], '%H:%M')
            t2 = datetime.strptime(str(s.hora_fin)[:5], '%H:%M')
            delta = (t2 - t1).total_seconds() / 3600
            return round(delta, 2) if delta > 0 else 0
        except Exception:
            return 0
    horas_total = sum(_hr_plan(s) for s in
                      Sesion.objects.filter(docente=docente, cohorte=cohorte)
                      .exclude(estado='cancelada'))

    institucion = cohorte.curso.institucion if cohorte.curso else None
    ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    pago = PagoDocente.objects.create(
        docente=docente, cohorte=cohorte, institucion=institucion,
        horas_dictadas=round(horas_total, 2),
        monto=monto,
        observacion=observacion,
        tipo_pago='horas',
        estado='pagado',
        metodo_pago=metodo,
        comprobante=comprobante if comprobante else None,
        fecha_pago=ahora,
    )

    Notificacion.notificar(
        usuario_id=docente.usuario_id,
        titulo='Pago liquidado',
        mensaje=f'{institucion.nombre if institucion else "Sistema"} liquidó ₲ {int(monto):,}'.replace(',', '.'),
        tipo='success',
        url='/mi-salario/',
    )

    messages.success(request, f'Liquidación confirmada: ₲ {int(monto):,} a {docente.usuario.nombre_completo}.'.replace(',', '.'))
    return redirect('pagos_docentes')


@permiso_required('pagos.aprobar')
def marcar_pagado_docente(request, pk):
    """Liquidación del docente: el tesorero adjunta comprobante y método de pago,
    se notifica al docente y el registro queda cerrado para auditoría."""
    pago = get_object_or_404(PagoDocente.objects.select_related(
        'docente__usuario', 'institucion', 'cohorte__curso'
    ), pk=pk)

    if request.method != 'POST':
        return redirect('pagos_docentes')

    if pago.estado != 'pendiente':
        messages.warning(request, 'El pago no está en estado pendiente.')
        return redirect('pagos_docentes')

    metodo = (request.POST.get('metodo_pago') or '').strip()
    metodos_validos = {'transferencia', 'cheque', 'efectivo'}
    if metodo not in metodos_validos:
        messages.error(request, 'Seleccioná un método de pago válido.')
        return redirect('pagos_docentes')

    comprobante = request.FILES.get('comprobante')
    # El comprobante es obligatorio cuando es transferencia o cheque
    if metodo in ('transferencia', 'cheque') and not comprobante:
        messages.error(request, f'Adjuntá el comprobante del {metodo}.')
        return redirect('pagos_docentes')

    if comprobante:
        ext = (comprobante.name.rsplit('.', 1)[-1] or '').lower()
        if ext not in ('pdf', 'jpg', 'jpeg', 'png'):
            messages.error(request, 'El comprobante debe ser PDF, JPG o PNG.')
            return redirect('pagos_docentes')
        if comprobante.size > 5 * 1024 * 1024:
            messages.error(request, 'El comprobante no debe superar 5 MB.')
            return redirect('pagos_docentes')
        pago.comprobante = comprobante

    pago.metodo_pago = metodo
    pago.estado = 'pagado'
    pago.fecha_pago = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pago.save()

    # Notificar al docente
    inst_nombre = pago.institucion.nombre if pago.institucion else '—'
    Notificacion.notificar(
        usuario_id=pago.docente.usuario_id,
        titulo='Pago liquidado',
        mensaje=f'{inst_nombre} liquidó tu pago de ₲ {int(pago.monto):,}'.replace(',', '.'),
        tipo='success',
        url='/mi-salario/',
    )

    messages.success(request, f'Liquidación confirmada. Se notificó al docente.')
    return redirect('pagos_docentes')


@permiso_required('pagos.anular')
def anular_pago_docente(request, pk):
    pago = get_object_or_404(PagoDocente, pk=pk)
    if request.method == 'POST':
        if pago.estado != 'anulado':
            pago.estado = 'anulado'
            pago.save()
            messages.success(request, 'Pago anulado.')
        else:
            messages.warning(request, 'El pago ya está anulado.')
    return redirect('pagos_docentes')