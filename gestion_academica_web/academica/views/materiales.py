from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from ..decorators import permiso_required, get_usuario_sesion, tiene_permiso_ctx
from ..models import Cohorte, Material, Docente, Inscripcion, Notificacion


def _docente_de(usuario):
    if usuario.get('rol') == 'docente' and usuario.get('perfil_id'):
        try:
            return Docente.objects.get(pk=usuario['perfil_id'])
        except Docente.DoesNotExist:
            return None
    return None


@permiso_required('materiales.ver')
def lista_por_cohorte(request, cohorte_id):
    usuario = get_usuario_sesion(request)
    cohorte = get_object_or_404(Cohorte.objects.select_related('curso'), pk=cohorte_id)

    # Estudiante solo puede ver materiales de cohortes en las que está inscripto
    if usuario['rol'] == 'estudiante':
        inscripto = Inscripcion.objects.filter(
            estudiante_id=usuario.get('perfil_id'),
            cohorte_id=cohorte.id,
            estado='activa',
        ).exists()
        if not inscripto:
            messages.error(request, 'No estás inscripto en esta cohorte.')
            return redirect('catalogo')

    qs = (Material.objects
          .filter(cohorte=cohorte, activo=1)
          .select_related('docente__usuario')
          .order_by('-fecha_publicacion', '-id'))
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    puede_gestionar = tiene_permiso_ctx(usuario.get('rol'), 'materiales.gestionar')

    return render(request, 'materiales/list.html', {
        'usuario': usuario,
        'cohorte': cohorte,
        'materiales': page_obj,
        'page_obj': page_obj,
        'querystring': '',
        'puede_gestionar': puede_gestionar,
    })


@permiso_required('materiales.gestionar')
def nuevo(request, cohorte_id):
    usuario = get_usuario_sesion(request)
    cohorte = get_object_or_404(Cohorte, pk=cohorte_id)

    if request.method == 'POST':
        titulo = (request.POST.get('titulo') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip() or None
        url_externa = (request.POST.get('url_externa') or '').strip() or None
        archivo = request.FILES.get('archivo')

        if not titulo:
            messages.error(request, 'El título es obligatorio.')
            return redirect('materiales_nuevo', cohorte_id=cohorte.id)
        if not archivo and not url_externa:
            messages.error(request, 'Debe adjuntar un archivo o una URL externa.')
            return redirect('materiales_nuevo', cohorte_id=cohorte.id)

        material = Material.objects.create(
            cohorte=cohorte,
            docente=_docente_de(usuario),
            titulo=titulo,
            descripcion=descripcion,
            archivo=archivo,
            url_externa=url_externa,
            fecha_publicacion=date.today().isoformat(),
            activo=1,
        )
        # Notificar a estudiantes inscriptos
        url_destino = f'/cohortes/{cohorte.id}/materiales/'
        inscriptos = Inscripcion.objects.filter(
            cohorte=cohorte, estado='activa'
        ).select_related('estudiante__usuario')
        for ins in inscriptos:
            Notificacion.notificar(
                usuario_id=ins.estudiante.usuario_id,
                titulo='Nuevo material disponible',
                mensaje=f'{cohorte.nombre}: "{titulo}"',
                tipo='info',
                url=url_destino,
            )
        messages.success(request, 'Material publicado.')
        return redirect('materiales_cohorte', cohorte_id=cohorte.id)

    return render(request, 'materiales/form.html', {
        'usuario': usuario,
        'cohorte': cohorte,
    })


@permiso_required('materiales.gestionar')
@require_POST
def eliminar(request, cohorte_id, pk):
    material = get_object_or_404(Material, pk=pk, cohorte_id=cohorte_id)
    material.activo = 0
    material.save()
    messages.success(request, 'Material eliminado.')
    return redirect('materiales_cohorte', cohorte_id=cohorte_id)
