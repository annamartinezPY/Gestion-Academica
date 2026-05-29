from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.core.paginator import Paginator

from ..decorators import login_required, get_usuario_sesion
from ..models import Notificacion


@login_required
def lista(request):
    usuario = get_usuario_sesion(request)
    qs = (Notificacion.objects
          .filter(usuario_id=usuario['id'])
          .order_by('-fecha', '-id'))
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'notificaciones/list.html', {
        'usuario': usuario,
        'notificaciones': page_obj,
        'page_obj': page_obj,
        'querystring': '',
    })


@login_required
@require_POST
def marcar_leida(request, pk):
    n = get_object_or_404(Notificacion, pk=pk, usuario_id=request.session.get('usuario_id'))
    n.leida = 1
    n.save()
    if n.url:
        return redirect(n.url)
    return redirect('notificaciones_lista')


@login_required
@require_POST
def marcar_todas(request):
    Notificacion.objects.filter(
        usuario_id=request.session.get('usuario_id'), leida=0
    ).update(leida=1)
    messages.success(request, 'Todas marcadas como leídas.')
    return redirect('notificaciones_lista')


@login_required
def abrir(request, pk):
    """GET: marca como leída y redirige a la URL destino."""
    n = get_object_or_404(Notificacion, pk=pk, usuario_id=request.session.get('usuario_id'))
    n.leida = 1
    n.save()
    return redirect(n.url or 'notificaciones_lista')
