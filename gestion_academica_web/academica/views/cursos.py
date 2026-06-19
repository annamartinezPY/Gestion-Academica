from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..decorators import permiso_required, get_usuario_sesion
from ..models import Curso, Modalidad, Institucion, CursoCondicion
from ..forms import CursoForm


def _fmt_guaranies(valor):
    """50000 → '50.000' (entero con separador de miles tipo guaraní)."""
    try:
        return f'{int(round(float(valor or 0))):,}'.replace(',', '.')
    except (TypeError, ValueError):
        return '0'


def _sincronizar_condiciones(curso, condiciones_seleccionadas):
    """Reemplaza las CursoCondicion de un curso por las nuevas condiciones seleccionadas,
    y refresca `condiciones_ingreso` con el texto derivado (para mostrar en el catálogo)."""
    # Borrar las relaciones previas y volver a crear (más simple que diffear)
    CursoCondicion.objects.filter(curso=curso).delete()
    for c in condiciones_seleccionadas:
        CursoCondicion.objects.create(curso=curso, condicion=c)

    # Texto derivado para vistas que muestran condiciones_ingreso (catálogo del estudiante)
    if condiciones_seleccionadas:
        lineas = []
        for c in condiciones_seleccionadas:
            if c.descripcion:
                lineas.append(f'• {c.nombre}: {c.descripcion}')
            else:
                lineas.append(f'• {c.nombre}')
        curso.condiciones_ingreso = '\n'.join(lineas)
    else:
        curso.condiciones_ingreso = None
    curso.save()


@permiso_required('cursos.ver')
def lista(request):
    q             = (request.GET.get('q') or '').strip()
    modalidad_id  = (request.GET.get('modalidad') or '').strip()
    institucion_id = (request.GET.get('institucion') or '').strip()

    cursos = (Curso.objects
              .select_related('modalidad', 'institucion')
              .filter(activo=1))

    if q:
        cursos = cursos.filter(
            Q(nombre__icontains=q) |
            Q(codigo__icontains=q) |
            Q(descripcion__icontains=q)
        )
    if modalidad_id.isdigit():
        cursos = cursos.filter(modalidad_id=int(modalidad_id))
    if institucion_id.isdigit():
        cursos = cursos.filter(institucion_id=int(institucion_id))

    cursos = cursos.order_by('nombre')

    paginator = Paginator(cursos, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    qs_parts = []
    if q: qs_parts.append(f'q={q}')
    if modalidad_id: qs_parts.append(f'modalidad={modalidad_id}')
    if institucion_id: qs_parts.append(f'institucion={institucion_id}')

    return render(request, 'cursos/list.html', {
        'cursos': page_obj,
        'page_obj': page_obj,
        'querystring': '&'.join(qs_parts),
        'modalidades': Modalidad.objects.order_by('nombre'),
        'instituciones': Institucion.objects.filter(activo=1).order_by('nombre'),
        'filtros': {
            'q': q,
            'modalidad': modalidad_id,
            'institucion': institucion_id,
        },
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('cursos.crear')
def nuevo(request):
    form = CursoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        curso = Curso.objects.create(
            nombre=d['nombre'],
            descripcion=d.get('descripcion') or '',
            institucion=d['institucion'],
            modalidad=d['modalidad'],
            horas_totales=d.get('horas_totales') or 0,
            tarifa_estudiante=d.get('tarifa_estudiante') or 0.0,
            activo=1,
        )
        _sincronizar_condiciones(curso, d.get('condiciones') or [])
        messages.success(request, f'Curso "{d["nombre"]}" creado.')
        return redirect('cursos_lista')
    return render(request, 'cursos/form.html', {
        'form': form, 'titulo': 'Nuevo Curso',
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('cursos.editar')
def editar(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    condiciones_actuales = list(
        CursoCondicion.objects.filter(curso=curso).values_list('condicion_id', flat=True)
    )
    initial = {
        'nombre': curso.nombre,
        'descripcion': curso.descripcion,
        'institucion': curso.institucion,
        'modalidad': curso.modalidad,
        'horas_totales': curso.horas_totales,
        'tarifa_estudiante': _fmt_guaranies(curso.tarifa_estudiante),
        'condiciones': condiciones_actuales,
    }
    form = CursoForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        curso.nombre = d['nombre']
        curso.descripcion = d.get('descripcion') or ''
        curso.institucion = d['institucion']
        curso.modalidad = d['modalidad']
        curso.horas_totales = d.get('horas_totales') or 0
        curso.tarifa_estudiante = d.get('tarifa_estudiante') or 0.0
        curso.save()
        _sincronizar_condiciones(curso, d.get('condiciones') or [])
        messages.success(request, 'Curso actualizado.')
        return redirect('cursos_lista')
    return render(request, 'cursos/form.html', {
        'form': form, 'titulo': 'Editar Curso', 'curso': curso,
        'usuario': get_usuario_sesion(request),
    })


@permiso_required('cursos.desactivar')
def desactivar(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == 'POST':
        curso.activo = 0
        curso.save()
        messages.success(request, f'Curso "{curso.nombre}" desactivado.')
    return redirect('cursos_lista')