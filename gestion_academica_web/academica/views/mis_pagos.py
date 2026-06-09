import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from ..decorators import login_required, get_usuario_sesion
from ..models import Estudiante, PagoEstudiante, Inscripcion


METODOS = [
    ('efectivo',     'Efectivo',      'bi-cash-coin',       'success'),
    ('transferencia','Transferencia', 'bi-bank',            'primary'),
]


# Restricciones para el comprobante de transferencia
COMPROBANTE_EXT_VALIDAS = {'pdf', 'jpg', 'jpeg', 'png'}
COMPROBANTE_TAM_MAX_MB = 5


@login_required
def mis_pagos(request):
    usuario = get_usuario_sesion(request)
    if usuario['rol'] != 'estudiante':
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')

    try:
        estudiante = Estudiante.objects.select_related('usuario').get(pk=usuario['perfil_id'])
    except Estudiante.DoesNotExist:
        messages.error(request, 'Perfil de estudiante no encontrado.')
        return redirect('dashboard')

    pagos = (PagoEstudiante.objects
             .filter(inscripcion__estudiante=estudiante)
             .select_related('inscripcion__cohorte__curso')
             .order_by('-fecha_pago'))

    inscripciones_activas = (Inscripcion.objects
                              .filter(estudiante=estudiante, estado='activa')
                              .select_related('cohorte__curso'))

    total_pagado = sum(p.monto for p in pagos if p.estado in ('aprobado', 'pagado'))
    pendientes   = sum(p.monto for p in pagos if p.estado in ('pendiente', 'en_revision'))

    return render(request, 'pagos/mis_pagos.html', {
        'usuario': usuario,
        'estudiante': estudiante,
        'pagos': pagos,
        'inscripciones_activas': inscripciones_activas,
        'total_pagado': total_pagado,
        'pendientes': pendientes,
        'metodos': METODOS,
    })


@login_required
def registrar_pago(request):
    usuario = get_usuario_sesion(request)
    if usuario['rol'] != 'estudiante':
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')

    if request.method != 'POST':
        return redirect('mis_pagos')

    try:
        estudiante = Estudiante.objects.get(pk=usuario['perfil_id'])
    except Estudiante.DoesNotExist:
        messages.error(request, 'Perfil no encontrado.')
        return redirect('dashboard')

    inscripcion_id = request.POST.get('inscripcion_id')
    monto_raw      = request.POST.get('monto', '').strip()
    metodo         = request.POST.get('metodo_pago', '').strip()
    referencia     = request.POST.get('referencia', '').strip()
    observacion    = request.POST.get('observacion', '').strip()
    comprobante    = request.FILES.get('comprobante')

    # Validaciones
    metodos_validos = [m[0] for m in METODOS]
    if metodo not in metodos_validos:
        messages.error(request, 'Método de pago inválido.')
        return redirect('mis_pagos')

    try:
        monto = float(monto_raw.replace('.', '').replace(',', '') if monto_raw else 0)
        if monto <= 0:
            raise ValueError
    except ValueError:
        messages.error(request, 'El monto debe ser un número mayor a cero.')
        return redirect('mis_pagos')

    try:
        inscripcion = Inscripcion.objects.get(pk=inscripcion_id, estudiante=estudiante, estado='activa')
    except Inscripcion.DoesNotExist:
        messages.error(request, 'Inscripción no encontrada.')
        return redirect('mis_pagos')

    if metodo == 'transferencia':
        if not referencia:
            messages.error(request, 'Para transferencia debe ingresar el número de referencia.')
            return redirect('mis_pagos')
        if not comprobante:
            messages.error(request, 'Para transferencia debe adjuntar el comprobante (PDF o imagen).')
            return redirect('mis_pagos')
        # Validar tipo y tamaño
        ext = (comprobante.name.rsplit('.', 1)[-1] or '').lower()
        if ext not in COMPROBANTE_EXT_VALIDAS:
            messages.error(
                request,
                f'El comprobante debe ser PDF, JPG o PNG (recibido: .{ext}).'
            )
            return redirect('mis_pagos')
        if comprobante.size > COMPROBANTE_TAM_MAX_MB * 1024 * 1024:
            messages.error(
                request,
                f'El comprobante no debe superar {COMPROBANTE_TAM_MAX_MB} MB.'
            )
            return redirect('mis_pagos')
    else:
        # Si el método es efectivo se ignora cualquier archivo subido
        comprobante = None

    PagoEstudiante.objects.create(
        inscripcion=inscripcion,
        monto=monto,
        metodo_pago=metodo,
        referencia=referencia or None,
        observacion=observacion or '',
        fecha_pago=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        estado='pendiente',
        comprobante=comprobante,
    )

    messages.success(request, 'Pago registrado. Quedará pendiente hasta que sea confirmado por el administrador.')
    return redirect('mis_pagos')
