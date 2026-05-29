from datetime import datetime, date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from ..decorators import permiso_required, get_usuario_sesion
from ..models import Cohorte, Sesion, Asistencia, Inscripcion


def _hora_actual():
    return datetime.now().strftime('%H:%M:%S')


def _fecha_hoy_iso():
    return date.today().isoformat()


@permiso_required('asistencias.marcar')
@require_POST
def iniciar_sesion(request, pk, sesion_pk):
    sesion = get_object_or_404(Sesion, pk=sesion_pk, cohorte_id=pk)
    if sesion.estado not in (None, '', 'planificada'):
        messages.warning(request, 'La sesión ya fue iniciada.')
        return redirect('cohortes_detalle', pk=pk)
    sesion.hora_inicio_real = _hora_actual()
    sesion.estado = 'en_curso'
    sesion.save()
    messages.success(request, f'Sesión iniciada a las {sesion.hora_inicio_real[:5]}.')
    return redirect('asistencia_marcar', pk=pk, sesion_pk=sesion_pk)


@permiso_required('asistencias.marcar')
@require_POST
def finalizar_sesion(request, pk, sesion_pk):
    sesion = get_object_or_404(Sesion, pk=sesion_pk, cohorte_id=pk)
    if sesion.estado != 'en_curso':
        messages.warning(request, 'La sesión no está en curso.')
        return redirect('cohortes_detalle', pk=pk)
    sesion.hora_fin_real = _hora_actual()
    sesion.estado = 'finalizada'
    sesion.save()
    messages.success(request, f'Sesión finalizada. Horas dictadas: {sesion.horas_dictadas}h')
    return redirect('cohortes_detalle', pk=pk)


@permiso_required('asistencias.marcar')
def marcar(request, pk, sesion_pk):
    """Vista de marcación de asistencia: lista de inscriptos activos
    + check presente/ausente + observación. Guarda todo al confirmar."""
    cohorte = get_object_or_404(Cohorte.objects.select_related('curso'), pk=pk)
    sesion = get_object_or_404(
        Sesion.objects.select_related('docente__usuario'),
        pk=sesion_pk, cohorte_id=pk,
    )

    # Inscriptos activos de la cohorte
    inscripciones = (Inscripcion.objects
                     .filter(cohorte=cohorte, estado='activa')
                     .select_related('estudiante__usuario')
                     .order_by('estudiante__usuario__apellido',
                               'estudiante__usuario__nombre'))

    # Asistencias ya registradas
    existentes = {a.estudiante_id: a
                  for a in Asistencia.objects.filter(sesion=sesion)}

    if request.method == 'POST':
        marca = _hora_actual()
        for ins in inscripciones:
            est = ins.estudiante
            presente = 1 if request.POST.get(f'presente_{est.id}') == '1' else 0
            obs = (request.POST.get(f'obs_{est.id}') or '').strip() or None
            existente = existentes.get(est.id)
            if existente:
                existente.presente = presente
                existente.observacion = obs
                if not existente.hora_marca:
                    existente.hora_marca = marca
                existente.save()
            else:
                Asistencia.objects.create(
                    sesion=sesion, estudiante=est,
                    presente=presente, observacion=obs,
                    hora_marca=marca,
                )
        messages.success(request, 'Asistencia registrada.')
        # Si la sesión sigue en_curso, redirige al detalle para que puedan finalizarla
        return redirect('cohortes_detalle', pk=pk)

    # Construir filas para el template
    filas = []
    for ins in inscripciones:
        est = ins.estudiante
        a = existentes.get(est.id)
        filas.append({
            'estudiante': est,
            'presente': True if (a is None or a.presente == 1) else False,
            'observacion': a.observacion if a else '',
            'hora_marca': a.hora_marca if a else '',
            'ya_marcado': a is not None,
        })

    return render(request, 'asistencia/marcar.html', {
        'usuario': get_usuario_sesion(request),
        'cohorte': cohorte,
        'sesion': sesion,
        'filas': filas,
        'total': len(filas),
    })
