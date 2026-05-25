from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum, Count, Q
from ..decorators import login_required, get_usuario_sesion
from ..models import Docente, PagoDocente


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
             .select_related('cohorte__curso')
             .order_by('-fecha_pago'))

    # KPIs
    total_cobrado  = pagos.filter(estado='pagado').aggregate(t=Sum('monto'))['t'] or 0
    total_pendiente = pagos.filter(estado='pendiente').aggregate(t=Sum('monto'))['t'] or 0
    total_sesiones  = docente.sesiones.count()

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

    return render(request, 'docentes/mi_salario.html', {
        'usuario': usuario,
        'docente': docente,
        'pagos': pagos,
        'total_cobrado': total_cobrado,
        'total_pendiente': total_pendiente,
        'total_sesiones': total_sesiones,
        'por_cohorte': por_cohorte,
        'por_tipo': por_tipo,
    })
