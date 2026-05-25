import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..decorators import permiso_required, get_usuario_sesion
from ..models import (
    PagoEstudiante, PagoDocente, Inscripcion,
    Docente, Cohorte, Estudiante, Usuario,
)
from ..forms import PagoEstudianteForm, PagoDocenteHorasForm, PagoDocenteMaterialesForm


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
    return render(request, 'pagos/lista_estudiantes.html', {
        'pagos': qs, 'cohortes': cohortes,
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
        messages.warning(request, f'Pago rechazado.')
    return redirect('pagos_estudiantes')


# ──────────────────────────────────────────────
#  Pagos a docentes
# ──────────────────────────────────────────────

@permiso_required('pagos.ver')
def lista_docentes(request):
    estado = request.GET.get('estado', '')
    qs = PagoDocente.objects.select_related(
        'docente__usuario', 'cohorte__curso'
    ).order_by('-fecha_pago')
    if estado:
        qs = qs.filter(estado=estado)
    total = sum(p.monto for p in qs if p.estado != 'anulado')
    pendiente = sum(p.monto for p in qs if p.estado == 'pendiente')
    return render(request, 'pagos/lista_docentes.html', {
        'pagos': qs, 'total': total, 'pendiente': pendiente,
        'filtro_estado': estado,
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('pagos.crear')
def nuevo_pago_docente(request):
    docentes = Docente.objects.select_related('usuario').filter(usuario__activo=1)
    cohortes = Cohorte.objects.select_related('curso').order_by('-fecha_inicio')
    tipo = request.GET.get('tipo', 'horas')

    if request.method == 'POST':
        tipo = request.POST.get('tipo', 'horas')
        docente_id = request.POST.get('docente_id')
        cohorte_id = request.POST.get('cohorte_id')

        try:
            docente = Docente.objects.select_related('usuario').get(pk=docente_id)
            cohorte = Cohorte.objects.get(pk=cohorte_id)
        except (Docente.DoesNotExist, Cohorte.DoesNotExist):
            messages.error(request, 'Docente o cohorte no encontrado.')
            return redirect('pagos_docentes')

        if tipo == 'horas':
            form = PagoDocenteHorasForm(request.POST)
            if form.is_valid():
                d = form.cleaned_data
                horas = d['horas_dictadas']
                monto = docente.tarifa_hora * horas
                PagoDocente.objects.create(
                    docente=docente, cohorte=cohorte,
                    horas_dictadas=horas, monto=monto,
                    observacion=d.get('observacion') or '',
                    fecha_pago=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    estado='pendiente', tipo_pago='horas',
                )
                messages.success(request, f'Pago por horas registrado: ${monto:.2f}')
                return redirect('pagos_docentes')
        else:
            form = PagoDocenteMaterialesForm(request.POST)
            if form.is_valid():
                d = form.cleaned_data
                PagoDocente.objects.create(
                    docente=docente, cohorte=cohorte,
                    horas_dictadas=0, monto=d['monto'],
                    concepto=d['concepto'],
                    observacion=d.get('observacion') or '',
                    fecha_pago=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    estado='pendiente', tipo_pago='materiales',
                )
                messages.success(request, f'Pago por materiales registrado: ${d["monto"]:.2f}')
                return redirect('pagos_docentes')
    else:
        form = PagoDocenteHorasForm() if tipo == 'horas' else PagoDocenteMaterialesForm()

    return render(request, 'pagos/form_docente.html', {
        'form': form, 'docentes': docentes, 'cohortes': cohortes, 'tipo': tipo,
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('pagos.aprobar')
def marcar_pagado_docente(request, pk):
    pago = get_object_or_404(PagoDocente, pk=pk)
    if request.method == 'POST':
        if pago.estado == 'pendiente':
            pago.estado = 'pagado'
            pago.save()
            messages.success(request, f'Pago de ${pago.monto:.2f} marcado como pagado.')
        else:
            messages.warning(request, 'El pago no está en estado pendiente.')
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