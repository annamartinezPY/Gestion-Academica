from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.db import connection

import datetime
from ..decorators import get_usuario_sesion, tiene_permiso_ctx
from ..models import (
    Institucion, Modalidad, Curso, InstitucionModalidad,
    CondicionInscripcion, CursoCondicion, DocenteInstitucion, Docente,
)
from ..forms import InstitucionForm


class AdminView(View):
    """Vista base con verificación de sesión y permiso granular."""
    permiso = None  # subclases sobreescriben con 'modulo.accion'

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('usuario_id'):
            return redirect('login')
        rol = request.session.get('rol')
        if self.permiso and not tiene_permiso_ctx(rol, self.permiso):
            messages.error(request, 'No tiene permisos para acceder a esta sección.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def ctx(self, request):
        return {'usuario': get_usuario_sesion(request)}


class InstitucionListView(AdminView):
    permiso = 'instituciones.ver'
    template = 'instituciones/list.html'

    def get(self, request):
        instituciones = (Institucion.objects
                         .prefetch_related('modalidades')
                         .order_by('nombre'))
        return render(request, self.template, {
            **self.ctx(request),
            'instituciones': instituciones,
        })


class InstitucionCreateView(AdminView):
    permiso = 'instituciones.crear'

    def _render(self, request, form):
        return render(request, 'instituciones/form.html', {
            **self.ctx(request),
            'form': form,
            'titulo': 'Nueva Institución',
        })

    def get(self, request):
        return self._render(request, InstitucionForm())

    def post(self, request):
        form = InstitucionForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data
            Institucion.objects.create(
                nombre=d['nombre'],
                email=d['email'],
                telefono=d['telefono'],
                direccion=d['direccion'],
                ciudad=d['ciudad'],
                imagen=d.get('imagen') or None,
                activo=1 if d['activo'] else 0,
            )
            messages.success(request, f'Institución "{d["nombre"]}" creada.')
            return redirect('instituciones_lista')
        return self._render(request, form)


class InstitucionDetailView(AdminView):
    """Detail + Edit unificados en /instituciones/<pk>/"""
    permiso = 'instituciones.ver'

    def _ctx_detalle(self, request, inst, form):
        cursos = (Curso.objects
                  .filter(institucion=inst)
                  .select_related('modalidad')
                  .prefetch_related('condiciones')
                  .order_by('nombre'))
        cursos_sin_asignar = (Curso.objects
                              .filter(institucion__isnull=True, activo=1)
                              .select_related('modalidad')
                              .order_by('nombre'))
        modalidades_disponibles = (Modalidad.objects
                                   .exclude(instituciones=inst)
                                   .order_by('nombre'))
        todas_modalidades = Modalidad.objects.order_by('nombre')
        condiciones = CondicionInscripcion.objects.filter(activo=1).order_by('texto')
        docentes_inst = (DocenteInstitucion.objects
                         .filter(institucion=inst)
                         .select_related('docente__usuario')
                         .order_by('docente__usuario__apellido'))
        docentes_ids_vinculados = set(docentes_inst.values_list('docente_id', flat=True))
        docentes_disponibles = (Docente.objects
                                .select_related('usuario')
                                .filter(usuario__activo=1)
                                .exclude(id__in=docentes_ids_vinculados)
                                .order_by('usuario__apellido'))
        return {
            **self.ctx(request),
            'inst': inst,
            'form': form,
            'cursos': cursos,
            'cursos_sin_asignar': cursos_sin_asignar,
            'modalidades_disponibles': modalidades_disponibles,
            'todas_modalidades': todas_modalidades,
            'condiciones': condiciones,
            'docentes_inst': docentes_inst,
            'docentes_disponibles': docentes_disponibles,
            'anio_actual': datetime.date.today().year,
        }

    def get(self, request, pk):
        inst = get_object_or_404(Institucion.objects.prefetch_related('modalidades'), pk=pk)
        initial = {
            'nombre': inst.nombre,
            'email': inst.email or '',
            'telefono': inst.telefono or '',
            'direccion': inst.direccion or '',
            'ciudad': inst.ciudad or '',
            'activo': bool(inst.activo),
        }
        form = InstitucionForm(initial=initial)
        return render(request, 'instituciones/detail.html', self._ctx_detalle(request, inst, form))

    def post(self, request, pk):
        inst = get_object_or_404(Institucion.objects.prefetch_related('modalidades'), pk=pk)
        form = InstitucionForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data
            inst.nombre = d['nombre']
            inst.email = d['email']
            inst.telefono = d['telefono']
            inst.direccion = d['direccion']
            inst.ciudad = d['ciudad']
            if d.get('imagen'):
                inst.imagen = d['imagen']
            # activo se maneja solo con el botón Desactivar, no desde este form
            inst.save()
            messages.success(request, 'Institución actualizada.')
            return redirect('instituciones_detalle', pk=pk)
        return render(request, 'instituciones/detail.html', self._ctx_detalle(request, inst, form))


class InstitucionDeactivateView(AdminView):
    permiso = 'instituciones.desactivar'

    def post(self, request, pk):
        inst = get_object_or_404(Institucion, pk=pk)
        inst.activo = 0
        inst.save()
        messages.success(request, f'Institución "{inst.nombre}" desactivada.')
        return redirect('instituciones_lista')


class InstitucionAsignarCursoView(AdminView):
    permiso = 'instituciones.editar'

    def post(self, request, pk):
        inst = get_object_or_404(Institucion, pk=pk)
        try:
            curso = Curso.objects.get(pk=request.POST.get('curso_id'))
            curso.institucion = inst
            curso.save()
            messages.success(request, f'Curso "{curso.nombre}" asignado.')
        except Curso.DoesNotExist:
            messages.error(request, 'Curso no encontrado.')
        return redirect('instituciones_detalle', pk=pk)


class InstitucionDesasignarCursoView(AdminView):
    permiso = 'instituciones.editar'

    def post(self, request, pk, curso_pk):
        try:
            curso = Curso.objects.get(pk=curso_pk, institucion_id=pk)
            curso.institucion = None
            curso.save()
            messages.success(request, f'Curso "{curso.nombre}" desasignado.')
        except Curso.DoesNotExist:
            messages.error(request, 'Curso no encontrado.')
        return redirect('instituciones_detalle', pk=pk)


class InstitucionCrearCursoView(AdminView):
    """Crea un curso nuevo directamente desde la página de la institución."""
    permiso = 'cursos.crear'

    def post(self, request, pk):
        inst = get_object_or_404(Institucion, pk=pk)
        codigo   = request.POST.get('codigo', '').strip().upper()
        nombre   = request.POST.get('nombre', '').strip()
        desc     = request.POST.get('descripcion', '').strip()
        mod_id   = request.POST.get('modalidad_id', '').strip()
        horas    = request.POST.get('horas_totales', '0').strip()
        costo    = request.POST.get('tarifa_estudiante', '0').strip()
        conds    = request.POST.getlist('condicion_ids')         # ids existentes
        nueva_cond = request.POST.get('nueva_condicion', '').strip()

        # Validaciones básicas
        if not nombre:
            messages.error(request, 'El nombre del curso es obligatorio.')
            return redirect('instituciones_detalle', pk=pk)
        if not desc:
            messages.error(request, 'La descripción del curso es obligatoria.')
            return redirect('instituciones_detalle', pk=pk)
        if not mod_id:
            messages.error(request, 'Debe seleccionar una modalidad.')
            return redirect('instituciones_detalle', pk=pk)
        if codigo and Curso.objects.filter(codigo=codigo).exists():
            messages.error(request, f'Ya existe un curso con el código "{codigo}".')
            return redirect('instituciones_detalle', pk=pk)

        try:
            modalidad = Modalidad.objects.get(pk=mod_id)
        except Modalidad.DoesNotExist:
            messages.error(request, 'Modalidad no válida.')
            return redirect('instituciones_detalle', pk=pk)

        curso = Curso.objects.create(
            codigo=codigo or None,
            nombre=nombre,
            descripcion=desc or None,
            modalidad=modalidad,
            institucion=inst,
            horas_totales=int(horas) if horas.isdigit() else 0,
            tarifa_estudiante=float(costo) if costo else 0.0,
            activo=1,
        )

        # Agregar condición nueva si se ingresó
        if nueva_cond:
            condicion, _ = CondicionInscripcion.objects.get_or_create(texto=nueva_cond, defaults={'activo': 1})
            CursoCondicion.objects.get_or_create(curso=curso, condicion=condicion)

        # Vincular condiciones seleccionadas
        for cid in conds:
            try:
                CursoCondicion.objects.get_or_create(curso=curso, condicion_id=int(cid))
            except (ValueError, CondicionInscripcion.DoesNotExist):
                pass

        messages.success(request, f'Curso "{nombre}" creado y asignado a {inst.nombre}.')
        return redirect('instituciones_detalle', pk=pk)


class InstitucionDocenteView(AdminView):
    """Gestiona el vínculo docente ↔ institución."""
    permiso = 'instituciones.editar'

    def post(self, request, pk):
        inst = get_object_or_404(Institucion, pk=pk)
        accion     = request.POST.get('accion')
        docente_id = request.POST.get('docente_id')

        if accion == 'agregar':
            try:
                docente = Docente.objects.get(pk=docente_id)
                DocenteInstitucion.objects.get_or_create(docente=docente, institucion=inst)
                messages.success(request, f'Docente {docente.usuario.nombre_completo} vinculado.')
            except Docente.DoesNotExist:
                messages.error(request, 'Docente no encontrado.')
        elif accion == 'quitar':
            DocenteInstitucion.objects.filter(docente_id=docente_id, institucion=inst).delete()
            messages.success(request, 'Docente desvinculado.')

        return redirect('instituciones_detalle', pk=pk)


class InstitucionModalidadView(AdminView):
    permiso = 'instituciones.editar'

    def post(self, request, pk):
        inst = get_object_or_404(Institucion, pk=pk)
        accion = request.POST.get('accion')
        modalidad_id = request.POST.get('modalidad_id')

        if accion == 'agregar':
            # get_or_create falla porque la tabla no tiene columna 'id' (PK compuesta)
            if not InstitucionModalidad.objects.filter(
                institucion=inst, modalidad_id=modalidad_id
            ).exists():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO institucion_modalidades (institucion_id, modalidad_id) VALUES (?, ?)",
                        [inst.id, modalidad_id],
                    )
            messages.success(request, 'Modalidad agregada.')
        elif accion == 'quitar':
            InstitucionModalidad.objects.filter(
                institucion=inst, modalidad_id=modalidad_id
            ).delete()
            messages.success(request, 'Modalidad quitada.')
        else:
            messages.error(request, 'Acción no reconocida.')

        return redirect('instituciones_detalle', pk=pk)
