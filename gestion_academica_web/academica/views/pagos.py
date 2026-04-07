import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..decorators import rol_required, get_usuario_sesion
from ..models import (
    PagoEstudiante, PagoDocente, Inscripcion,
    Docente, Cohorte, Estudiante,
)
from ..forms import PagoEstudianteForm, PagoDocenteHorasForm, PagoDocenteMaterialesForm


# ──────────────────────────────────────────────
#  Pagos de estudiantes
# ──────────────────────────────────────────────

@rol_required('admin')
def lista_estudiantes(request):
    cohorte_id = request.GET.get('cohorte')
    qs = PagoEstudiante.objects.select_related(
        'inscripcion__estudiante__usuario',
        'inscripcion__cohorte__curso',
    ).order_by('-fecha_pago')
    if cohorte_id:
        qs = qs.filter(inscripcion__cohorte_id=cohorte_id)
    cohortes = Cohorte.objects.select_related('curso').order_by('-fecha_inicio')
    total = sum(p.monto for p in qs if p.estado != 'anulado')
    return render(request, 'pagos/lista_estudiantes.html', {
        'pagos': qs, 'cohortes': cohortes,
        'filtro_cohorte': cohorte_id, 'total': total,
        'usuario': get_usuario_sesion(request),
    })


@rol_required('admin')
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


@rol_required('admin')
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


# ──────────────────────────────────────────────
#  Pagos a docentes
# ──────────────────────────────────────────────

@rol_required('admin')
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


@rol_required('admin')
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


@rol_required('admin')
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


@rol_required('admin')
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