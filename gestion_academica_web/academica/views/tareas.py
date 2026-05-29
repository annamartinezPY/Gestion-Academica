from datetime import date, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from ..decorators import permiso_required, get_usuario_sesion, tiene_permiso_ctx
from ..models import Cohorte, Tarea, EntregaTarea, Docente, Estudiante, Inscripcion, Notificacion


def _docente_de(usuario):
    if usuario.get('rol') == 'docente' and usuario.get('perfil_id'):
        try:
            return Docente.objects.get(pk=usuario['perfil_id'])
        except Docente.DoesNotExist:
            return None
    return None


def _estudiante_de(usuario):
    if usuario.get('rol') == 'estudiante' and usuario.get('perfil_id'):
        try:
            return Estudiante.objects.get(pk=usuario['perfil_id'])
        except Estudiante.DoesNotExist:
            return None
    return None


@permiso_required('tareas.ver')
def lista_por_cohorte(request, cohorte_id):
    usuario = get_usuario_sesion(request)
    cohorte = get_object_or_404(Cohorte.objects.select_related('curso'), pk=cohorte_id)

    estudiante = _estudiante_de(usuario)
    if usuario['rol'] == 'estudiante':
        inscripto = Inscripcion.objects.filter(
            estudiante=estudiante, cohorte=cohorte, estado='activa'
        ).exists() if estudiante else False
        if not inscripto:
            messages.error(request, 'No estás inscripto en esta cohorte.')
            return redirect('catalogo')

    qs = (Tarea.objects
          .filter(cohorte=cohorte, activo=1)
          .select_related('docente__usuario')
          .order_by('-fecha_creacion', '-id'))
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Para estudiante: mapa de tarea_id -> EntregaTarea
    entregas_map = {}
    if estudiante:
        entregas_map = {
            e.tarea_id: e
            for e in EntregaTarea.objects.filter(
                tarea__in=qs, estudiante=estudiante,
            )
        }
    # Para docente: cantidad de entregas por tarea
    conteos = {}
    if usuario['rol'] in ('docente', 'admin'):
        for t in qs:
            conteos[t.id] = EntregaTarea.objects.filter(tarea=t).count()

    filas = []
    for t in page_obj.object_list:
        filas.append({
            'tarea': t,
            'entrega': entregas_map.get(t.id),
            'total_entregas': conteos.get(t.id, 0),
        })

    puede_gestionar = tiene_permiso_ctx(usuario.get('rol'), 'tareas.gestionar')
    puede_entregar = tiene_permiso_ctx(usuario.get('rol'), 'tareas.entregar') and estudiante is not None

    return render(request, 'tareas/list.html', {
        'usuario': usuario,
        'cohorte': cohorte,
        'page_obj': page_obj,
        'filas': filas,
        'querystring': '',
        'puede_gestionar': puede_gestionar,
        'puede_entregar': puede_entregar,
    })


@permiso_required('tareas.gestionar')
def nueva(request, cohorte_id):
    usuario = get_usuario_sesion(request)
    cohorte = get_object_or_404(Cohorte, pk=cohorte_id)

    if request.method == 'POST':
        titulo = (request.POST.get('titulo') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip() or None
        fecha_entrega = (request.POST.get('fecha_entrega') or '').strip() or None
        puntos = request.POST.get('puntos_maximos') or '100'
        archivo = request.FILES.get('archivo_consigna')

        if not titulo:
            messages.error(request, 'El título es obligatorio.')
            return redirect('tareas_nueva', cohorte_id=cohorte.id)
        try:
            puntos = int(puntos)
        except ValueError:
            puntos = 100

        tarea = Tarea.objects.create(
            cohorte=cohorte,
            docente=_docente_de(usuario),
            titulo=titulo,
            descripcion=descripcion,
            archivo_consigna=archivo,
            fecha_entrega=fecha_entrega,
            puntos_maximos=puntos,
            fecha_creacion=date.today().isoformat(),
            activo=1,
        )
        # Notificar a estudiantes inscriptos
        url_destino = f'/cohortes/{cohorte.id}/tareas/'
        inscriptos = Inscripcion.objects.filter(
            cohorte=cohorte, estado='activa'
        ).select_related('estudiante__usuario')
        for ins in inscriptos:
            Notificacion.notificar(
                usuario_id=ins.estudiante.usuario_id,
                titulo='Nueva tarea asignada',
                mensaje=f'{cohorte.nombre}: "{titulo}"' + (f' — vence {fecha_entrega}' if fecha_entrega else ''),
                tipo='warning',
                url=url_destino,
            )
        messages.success(request, 'Tarea creada.')
        return redirect('tareas_cohorte', cohorte_id=cohorte.id)

    return render(request, 'tareas/form.html', {
        'usuario': usuario,
        'cohorte': cohorte,
    })


@permiso_required('tareas.gestionar')
@require_POST
def eliminar(request, cohorte_id, pk):
    tarea = get_object_or_404(Tarea, pk=pk, cohorte_id=cohorte_id)
    tarea.activo = 0
    tarea.save()
    messages.success(request, 'Tarea eliminada.')
    return redirect('tareas_cohorte', cohorte_id=cohorte_id)


@permiso_required('tareas.entregar')
def entregar(request, cohorte_id, pk):
    usuario = get_usuario_sesion(request)
    estudiante = _estudiante_de(usuario)
    if not estudiante:
        messages.error(request, 'Solo estudiantes pueden entregar tareas.')
        return redirect('tareas_cohorte', cohorte_id=cohorte_id)

    tarea = get_object_or_404(Tarea, pk=pk, cohorte_id=cohorte_id, activo=1)
    # Validar inscripción
    inscripto = Inscripcion.objects.filter(
        estudiante=estudiante, cohorte_id=cohorte_id, estado='activa'
    ).exists()
    if not inscripto:
        messages.error(request, 'No estás inscripto en esta cohorte.')
        return redirect('catalogo')

    entrega = EntregaTarea.objects.filter(tarea=tarea, estudiante=estudiante).first()

    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        comentario = (request.POST.get('comentario') or '').strip() or None
        if not archivo and not (entrega and entrega.archivo):
            messages.error(request, 'Debe adjuntar un archivo.')
            return redirect('tareas_entregar', cohorte_id=cohorte_id, pk=tarea.id)

        ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if entrega:
            if archivo:
                entrega.archivo = archivo
            entrega.comentario = comentario
            entrega.fecha_entrega = ahora
            entrega.save()
            messages.success(request, 'Entrega actualizada.')
        else:
            EntregaTarea.objects.create(
                tarea=tarea, estudiante=estudiante,
                archivo=archivo, comentario=comentario,
                fecha_entrega=ahora,
            )
            messages.success(request, 'Tarea entregada.')
        return redirect('tareas_cohorte', cohorte_id=cohorte_id)

    return render(request, 'tareas/entregar.html', {
        'usuario': usuario,
        'cohorte': get_object_or_404(Cohorte, pk=cohorte_id),
        'tarea': tarea,
        'entrega': entrega,
    })


@permiso_required('tareas.gestionar')
def ver_entregas(request, cohorte_id, pk):
    usuario = get_usuario_sesion(request)
    tarea = get_object_or_404(Tarea.objects.select_related('cohorte__curso'),
                              pk=pk, cohorte_id=cohorte_id)

    entregas = (EntregaTarea.objects
                .filter(tarea=tarea)
                .select_related('estudiante__usuario')
                .order_by('estudiante__usuario__apellido'))

    if request.method == 'POST':
        # Guardar notas/feedback
        for e in entregas:
            nota_str = request.POST.get(f'nota_{e.id}', '').strip()
            fb = request.POST.get(f'feedback_{e.id}', '').strip() or None
            nota = None
            if nota_str:
                try:
                    nota = float(nota_str)
                except ValueError:
                    nota = None
            e.nota = nota
            e.feedback = fb
            e.save()
        messages.success(request, 'Calificaciones guardadas.')
        return redirect('tareas_entregas', cohorte_id=cohorte_id, pk=pk)

    return render(request, 'tareas/entregas.html', {
        'usuario': usuario,
        'cohorte': tarea.cohorte,
        'tarea': tarea,
        'entregas': entregas,
    })
