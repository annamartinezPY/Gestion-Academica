from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum, Count, Q
from ..decorators import login_required, get_usuario_sesion
from ..models import Docente, PagoDocente, Sesion


@login_required
def mi_salario(request):
    usuario = get_usuario_sesion(request)
    if usuario['rol'] != 'docente':
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')

    try:
        docente = Docente.objects.select_related('usuario').get(pk=usuario['perfil_id'])
    except Docente.DoesNotExist:
        messages.error(request, 'Perfil de docente no encontrado.')
        return redirect('dashboard')

    pagos = (PagoDocente.objects
             .filter(docente=docente)
             .select_related('cohorte__curso', 'institucion')
             .order_by('-fecha_pago'))

    # KPIs
    total_cobrado  = pagos.filter(estado='pagado').aggregate(t=Sum('monto'))['t'] or 0
    total_pendiente = pagos.filter(estado='pendiente').aggregate(t=Sum('monto'))['t'] or 0
    total_sesiones  = docente.sesiones.count()

    # --- Ledger de sesiones VERIFICADAS (finalizadas con hora_inicio_real y fin_real) ---
    sesiones_verificadas = (Sesion.objects
                            .filter(docente=docente, estado='finalizada')
                            .exclude(hora_inicio_real__isnull=True)
                            .exclude(hora_fin_real__isnull=True)
                            .select_related('cohorte__curso')
                            .order_by('-fecha', '-hora_inicio'))

    total_horas_verificadas = sum((s.horas_dictadas or 0) for s in sesiones_verificadas)

    # Resumen de horas verificadas por cohorte
    horas_por_cohorte = {}
    for s in sesiones_verificadas:
        key = (s.cohorte_id, s.cohorte.nombre, s.cohorte.curso.nombre)
        if key not in horas_por_cohorte:
            horas_por_cohorte[key] = {'sesiones': 0, 'horas': 0.0}
        horas_por_cohorte[key]['sesiones'] += 1
        horas_por_cohorte[key]['horas'] += (s.horas_dictadas or 0)
    ledger_por_cohorte = [
        {'cohorte_nombre': k[1], 'curso_nombre': k[2],
         'sesiones': v['sesiones'], 'horas': round(v['horas'], 2)}
        for k, v in horas_por_cohorte.items()
    ]
    ledger_por_cohorte.sort(key=lambda x: -x['horas'])

    # Resumen por cohorte
    por_cohorte = (PagoDocente.objects
                   .filter(docente=docente, estado='pagado')
                   .values('cohorte__nombre', 'cohorte__curso__nombre')
                   .annotate(total=Sum('monto'), sesiones=Count('id'))
                   .order_by('-total'))

    # Resumen por tipo de pago
    por_tipo = (PagoDocente.objects
                .filter(docente=docente, estado='pagado')
                .values('tipo_pago')
                .annotate(total=Sum('monto'), cantidad=Count('id'))
                .order_by('-total'))

    # Desglose por INSTITUCIÓN (multiinstitución): histórico de cobrado + pendiente
    por_institucion_pagado = (PagoDocente.objects
                              .filter(docente=docente, estado='pagado')
                              .values('institucion__id', 'institucion__nombre')
                              .annotate(total=Sum('monto'), cantidad=Count('id'))
                              .order_by('-total'))

    por_institucion_pendiente = (PagoDocente.objects
                                 .filter(docente=docente, estado='pendiente')
                                 .values('institucion__id', 'institucion__nombre')
                                 .annotate(total=Sum('monto'), cantidad=Count('id'))
                                 .order_by('-total'))

    # Próximos cobros: monto acumulado pendiente por institución
    proximos_cobros = list(por_institucion_pendiente)

    return render(request, 'docentes/mi_salario.html', {
        'usuario': usuario,
        'docente': docente,
        'pagos': pagos,
        'total_cobrado': total_cobrado,
        'total_pendiente': total_pendiente,
        'total_sesiones': total_sesiones,
        'por_cohorte': por_cohorte,
        'por_tipo': por_tipo,
        'sesiones_verificadas': sesiones_verificadas,
        'total_horas_verificadas': round(total_horas_verificadas, 2),
        'ledger_por_cohorte': ledger_por_cohorte,
        'por_institucion_pagado': list(por_institucion_pagado),
        'proximos_cobros': proximos_cobros,
    })
