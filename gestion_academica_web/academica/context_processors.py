from .models import Notificacion


def notificaciones_ctx(request):
    """Inyecta las últimas notificaciones del usuario en sesión a todos los templates."""
    usuario_id = request.session.get('usuario_id') if hasattr(request, 'session') else None
    if not usuario_id:
        return {'notif_count': 0, 'notif_recientes': []}
    try:
        recientes = list(
            Notificacion.objects
            .filter(usuario_id=usuario_id)
            .order_by('-fecha', '-id')[:5]
        )
        count = Notificacion.objects.filter(usuario_id=usuario_id, leida=0).count()
    except Exception:
        return {'notif_count': 0, 'notif_recientes': []}
    return {
        'notif_count': count,
        'notif_recientes': recientes,
    }
