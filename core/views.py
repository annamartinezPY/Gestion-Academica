"""
Vistas Django para el Sistema de Gestion Academica
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from decimal import Decimal
from datetime import date, timedelta
import json

from .models import (
    Usuario, Estudiante, Docente, Curso, Cohorte,
    Inscripcion, PagoEstudiante, PagoDocente, Sesion, Asistencia
)
from .forms import (
    LoginForm, CambiarPasswordForm, EstudianteForm, DocenteForm,
    CursoForm, CohorteForm, InscripcionForm, PagoEstudianteForm,
    PagoDocenteForm, SesionForm
)
from .decorators import admin_required, docente_required, estudiante_required


# =============================================================================
# AUTENTICACION
# =============================================================================

def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bienvenido/a, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contrasena incorrectos.')
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.info(request, 'Has cerrado sesion correctamente.')
    return redirect('login')


@login_required
def perfil(request):
    """Vista de perfil del usuario"""
    return render(request, 'core/perfil.html')


@login_required
def cambiar_password(request):
    """Vista para cambiar contrasena"""
    if request.method == 'POST':
        form = CambiarPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contrasena ha sido actualizada correctamente.')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor corrige los errores.')
    else:
        form = CambiarPasswordForm(request.user)
    
    return render(request, 'core/cambiar_password.html', {'form': form})


# =============================================================================
# DASHBOARD
# =============================================================================

@login_required
def dashboard(request):
    """Dashboard principal segun rol"""
    user = request.user
    context = {'user': user}
    
    if user.es_admin:
        # Estadisticas generales
        context['total_estudiantes'] = Estudiante.objects.filter(activo=True).count()
        context['total_docentes'] = Docente.objects.filter(activo=True).count()
        context['total_cursos'] = Curso.objects.filter(activo=True).count()
        context['cohortes_activas'] = Cohorte.objects.filter(estado='en_curso').count()
        
        # Ingresos del mes
        hoy = date.today()
        primer_dia_mes = hoy.replace(day=1)
        context['ingresos_mes'] = PagoEstudiante.objects.filter(
            estado='verificado',
            fecha_pago__gte=primer_dia_mes
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        # Pagos pendientes a docentes
        context['pagos_docentes_pendientes'] = PagoDocente.objects.filter(
            estado='pendiente'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        # Ultimas inscripciones
        context['ultimas_inscripciones'] = Inscripcion.objects.select_related(
            'estudiante', 'cohorte', 'cohorte__curso'
        ).order_by('-fecha_inscripcion')[:5]
        
        # Cohortes proximas a iniciar
        context['cohortes_proximas'] = Cohorte.objects.filter(
            estado='planificado',
            fecha_inicio__gte=hoy,
            fecha_inicio__lte=hoy + timedelta(days=30)
        ).select_related('curso', 'docente')[:5]
        
    elif user.es_docente:
        try:
            docente = user.docente_perfil
            context['docente'] = docente
            
            # Cohortes asignadas
            context['mis_cohortes'] = Cohorte.objects.filter(
                docente=docente
            ).select_related('curso').order_by('-fecha_inicio')[:5]
            
            # Proximas sesiones
            context['proximas_sesiones'] = Sesion.objects.filter(
                cohorte__docente=docente,
                fecha__gte=date.today()
            ).select_related('cohorte', 'cohorte__curso').order_by('fecha')[:5]
            
            # Pagos recibidos
            context['pagos_recibidos'] = PagoDocente.objects.filter(
                docente=docente,
                estado='pagado'
            ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            
        except Docente.DoesNotExist:
            messages.warning(request, 'Tu perfil de docente no esta configurado.')
            
    elif user.es_estudiante:
        try:
            estudiante = user.estudiante_perfil
            context['estudiante'] = estudiante
            
            # Mis inscripciones activas
            context['mis_inscripciones'] = Inscripcion.objects.filter(
                estudiante=estudiante,
                estado='activa'
            ).select_related('cohorte', 'cohorte__curso', 'cohorte__docente')
            
            # Saldo pendiente total
            inscripciones_activas = Inscripcion.objects.filter(
                estudiante=estudiante,
                estado='activa'
            )
            total_acordado = inscripciones_activas.aggregate(
                total=Sum('monto_acordado')
            )['total'] or Decimal('0.00')
            total_pagado = PagoEstudiante.objects.filter(
                inscripcion__in=inscripciones_activas,
                estado='verificado'
            ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            context['saldo_pendiente'] = total_acordado - total_pagado
            
            # Mis pagos recientes
            context['mis_pagos'] = PagoEstudiante.objects.filter(
                inscripcion__estudiante=estudiante
            ).select_related('inscripcion', 'inscripcion__cohorte').order_by('-fecha_pago')[:5]
            
        except Estudiante.DoesNotExist:
            messages.warning(request, 'Tu perfil de estudiante no esta configurado.')
    
    return render(request, 'core/dashboard.html', context)


# =============================================================================
# ESTUDIANTES
# =============================================================================

@login_required
@admin_required
def estudiante_list(request):
    """Lista de estudiantes"""
    query = request.GET.get('q', '')
    estudiantes = Estudiante.objects.all()
    
    if query:
        estudiantes = estudiantes.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(cedula__icontains=query) |
            Q(email__icontains=query)
        )
    
    paginator = Paginator(estudiantes, 15)
    page = request.GET.get('page')
    estudiantes = paginator.get_page(page)
    
    return render(request, 'core/estudiante_list.html', {
        'estudiantes': estudiantes,
        'query': query
    })


@login_required
@admin_required
def estudiante_create(request):
    """Crear estudiante"""
    if request.method == 'POST':
        form = EstudianteForm(request.POST)
        if form.is_valid():
            estudiante = form.save()
            messages.success(request, f'Estudiante {estudiante.nombre_completo} creado correctamente.')
            return redirect('estudiante_list')
    else:
        form = EstudianteForm()
    
    return render(request, 'core/estudiante_form.html', {
        'form': form,
        'titulo': 'Nuevo Estudiante'
    })


@login_required
def estudiante_detail(request, pk):
    """Detalle de estudiante"""
    estudiante = get_object_or_404(Estudiante, pk=pk)
    
    # Verificar permisos
    if not request.user.es_admin:
        if request.user.es_estudiante:
            try:
                if request.user.estudiante_perfil.pk != pk:
                    messages.error(request, 'No tienes permiso para ver este perfil.')
                    return redirect('dashboard')
            except Estudiante.DoesNotExist:
                messages.error(request, 'No tienes permiso para ver este perfil.')
                return redirect('dashboard')
        else:
            messages.error(request, 'No tienes permiso para ver este perfil.')
            return redirect('dashboard')
    
    inscripciones = estudiante.inscripciones.select_related(
        'cohorte', 'cohorte__curso', 'cohorte__docente'
    ).order_by('-fecha_inscripcion')
    
    pagos = PagoEstudiante.objects.filter(
        inscripcion__estudiante=estudiante
    ).select_related('inscripcion', 'inscripcion__cohorte').order_by('-fecha_pago')
    
    return render(request, 'core/estudiante_detail.html', {
        'estudiante': estudiante,
        'inscripciones': inscripciones,
        'pagos': pagos
    })


@login_required
@admin_required
def estudiante_update(request, pk):
    """Editar estudiante"""
    estudiante = get_object_or_404(Estudiante, pk=pk)
    
    if request.method == 'POST':
        form = EstudianteForm(request.POST, instance=estudiante)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estudiante actualizado correctamente.')
            return redirect('estudiante_detail', pk=pk)
    else:
        form = EstudianteForm(instance=estudiante)
    
    return render(request, 'core/estudiante_form.html', {
        'form': form,
        'estudiante': estudiante,
        'titulo': f'Editar: {estudiante.nombre_completo}'
    })


@login_required
@admin_required
def estudiante_delete(request, pk):
    """Eliminar estudiante"""
    estudiante = get_object_or_404(Estudiante, pk=pk)
    
    if request.method == 'POST':
        nombre = estudiante.nombre_completo
        estudiante.delete()
        messages.success(request, f'Estudiante {nombre} eliminado correctamente.')
        return redirect('estudiante_list')
    
    return render(request, 'core/estudiante_confirm_delete.html', {
        'estudiante': estudiante
    })


# =============================================================================
# DOCENTES
# =============================================================================

@login_required
@admin_required
def docente_list(request):
    """Lista de docentes"""
    query = request.GET.get('q', '')
    docentes = Docente.objects.all()
    
    if query:
        docentes = docentes.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(cedula__icontains=query) |
            Q(especialidad__icontains=query)
        )
    
    paginator = Paginator(docentes, 15)
    page = request.GET.get('page')
    docentes = paginator.get_page(page)
    
    return render(request, 'core/docente_list.html', {
        'docentes': docentes,
        'query': query
    })


@login_required
@admin_required
def docente_create(request):
    """Crear docente"""
    if request.method == 'POST':
        form = DocenteForm(request.POST)
        if form.is_valid():
            docente = form.save()
            messages.success(request, f'Docente {docente.nombre_completo} creado correctamente.')
            return redirect('docente_list')
    else:
        form = DocenteForm()
    
    return render(request, 'core/docente_form.html', {
        'form': form,
        'titulo': 'Nuevo Docente'
    })


@login_required
def docente_detail(request, pk):
    """Detalle de docente"""
    docente = get_object_or_404(Docente, pk=pk)
    
    # Verificar permisos
    if not request.user.es_admin:
        if request.user.es_docente:
            try:
                if request.user.docente_perfil.pk != pk:
                    messages.error(request, 'No tienes permiso para ver este perfil.')
                    return redirect('dashboard')
            except Docente.DoesNotExist:
                messages.error(request, 'No tienes permiso para ver este perfil.')
                return redirect('dashboard')
        else:
            messages.error(request, 'No tienes permiso para ver este perfil.')
            return redirect('dashboard')
    
    cohortes = docente.cohortes.select_related('curso').order_by('-fecha_inicio')
    pagos = docente.pagos_recibidos.select_related('cohorte').order_by('-fecha_pago')
    
    return render(request, 'core/docente_detail.html', {
        'docente': docente,
        'cohortes': cohortes,
        'pagos': pagos
    })


@login_required
@admin_required
def docente_update(request, pk):
    """Editar docente"""
    docente = get_object_or_404(Docente, pk=pk)
    
    if request.method == 'POST':
        form = DocenteForm(request.POST, instance=docente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Docente actualizado correctamente.')
            return redirect('docente_detail', pk=pk)
    else:
        form = DocenteForm(instance=docente)
    
    return render(request, 'core/docente_form.html', {
        'form': form,
        'docente': docente,
        'titulo': f'Editar: {docente.nombre_completo}'
    })


@login_required
@admin_required
def docente_delete(request, pk):
    """Eliminar docente"""
    docente = get_object_or_404(Docente, pk=pk)
    
    if request.method == 'POST':
        nombre = docente.nombre_completo
        docente.delete()
        messages.success(request, f'Docente {nombre} eliminado correctamente.')
        return redirect('docente_list')
    
    return render(request, 'core/docente_confirm_delete.html', {
        'docente': docente
    })


# =============================================================================
# CURSOS
# =============================================================================

@login_required
def curso_list(request):
    """Lista de cursos"""
    query = request.GET.get('q', '')
    cursos = Curso.objects.all()
    
    if query:
        cursos = cursos.filter(
            Q(nombre__icontains=query) |
            Q(codigo__icontains=query)
        )
    
    paginator = Paginator(cursos, 15)
    page = request.GET.get('page')
    cursos = paginator.get_page(page)
    
    return render(request, 'core/curso_list.html', {
        'cursos': cursos,
        'query': query
    })


@login_required
@admin_required
def curso_create(request):
    """Crear curso"""
    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            curso = form.save()
            messages.success(request, f'Curso {curso.nombre} creado correctamente.')
            return redirect('curso_list')
    else:
        form = CursoForm()
    
    return render(request, 'core/curso_form.html', {
        'form': form,
        'titulo': 'Nuevo Curso'
    })


@login_required
def curso_detail(request, pk):
    """Detalle de curso"""
    curso = get_object_or_404(Curso, pk=pk)
    cohortes = curso.cohortes.select_related('docente').order_by('-fecha_inicio')
    
    return render(request, 'core/curso_detail.html', {
        'curso': curso,
        'cohortes': cohortes
    })


@login_required
@admin_required
def curso_update(request, pk):
    """Editar curso"""
    curso = get_object_or_404(Curso, pk=pk)
    
    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso actualizado correctamente.')
            return redirect('curso_detail', pk=pk)
    else:
        form = CursoForm(instance=curso)
    
    return render(request, 'core/curso_form.html', {
        'form': form,
        'curso': curso,
        'titulo': f'Editar: {curso.nombre}'
    })


@login_required
@admin_required
def curso_delete(request, pk):
    """Eliminar curso"""
    curso = get_object_or_404(Curso, pk=pk)
    
    if request.method == 'POST':
        nombre = curso.nombre
        curso.delete()
        messages.success(request, f'Curso {nombre} eliminado correctamente.')
        return redirect('curso_list')
    
    return render(request, 'core/curso_confirm_delete.html', {
        'curso': curso
    })


# =============================================================================
# COHORTES
# =============================================================================

@login_required
def cohorte_list(request):
    """Lista de cohortes"""
    query = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    cohortes = Cohorte.objects.select_related('curso', 'docente')
    
    if query:
        cohortes = cohortes.filter(
            Q(codigo__icontains=query) |
            Q(curso__nombre__icontains=query)
        )
    
    if estado:
        cohortes = cohortes.filter(estado=estado)
    
    # Filtrar por docente si el usuario es docente
    if request.user.es_docente:
        try:
            cohortes = cohortes.filter(docente=request.user.docente_perfil)
        except Docente.DoesNotExist:
            cohortes = Cohorte.objects.none()
    
    paginator = Paginator(cohortes, 15)
    page = request.GET.get('page')
    cohortes = paginator.get_page(page)
    
    return render(request, 'core/cohorte_list.html', {
        'cohortes': cohortes,
        'query': query,
        'estado_filtro': estado,
        'estados': Cohorte.Estado.choices
    })


@login_required
@admin_required
def cohorte_create(request):
    """Crear cohorte"""
    if request.method == 'POST':
        form = CohorteForm(request.POST)
        if form.is_valid():
            cohorte = form.save()
            messages.success(request, f'Cohorte {cohorte.codigo} creada correctamente.')
            return redirect('cohorte_list')
    else:
        form = CohorteForm()
    
    return render(request, 'core/cohorte_form.html', {
        'form': form,
        'titulo': 'Nueva Cohorte'
    })


@login_required
def cohorte_detail(request, pk):
    """Detalle de cohorte"""
    cohorte = get_object_or_404(Cohorte.objects.select_related('curso', 'docente'), pk=pk)
    
    # Verificar permisos para docentes
    if request.user.es_docente:
        try:
            if cohorte.docente != request.user.docente_perfil:
                messages.error(request, 'No tienes permiso para ver esta cohorte.')
                return redirect('cohorte_list')
        except Docente.DoesNotExist:
            messages.error(request, 'No tienes permiso para ver esta cohorte.')
            return redirect('cohorte_list')
    
    inscripciones = cohorte.inscripciones.select_related('estudiante').order_by('estudiante__apellido')
    sesiones = cohorte.sesiones.order_by('numero_sesion')
    
    return render(request, 'core/cohorte_detail.html', {
        'cohorte': cohorte,
        'inscripciones': inscripciones,
        'sesiones': sesiones
    })


@login_required
@admin_required
def cohorte_update(request, pk):
    """Editar cohorte"""
    cohorte = get_object_or_404(Cohorte, pk=pk)
    
    if request.method == 'POST':
        form = CohorteForm(request.POST, instance=cohorte)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cohorte actualizada correctamente.')
            return redirect('cohorte_detail', pk=pk)
    else:
        form = CohorteForm(instance=cohorte)
    
    return render(request, 'core/cohorte_form.html', {
        'form': form,
        'cohorte': cohorte,
        'titulo': f'Editar: {cohorte.codigo}'
    })


@login_required
@admin_required
def cohorte_delete(request, pk):
    """Eliminar cohorte"""
    cohorte = get_object_or_404(Cohorte, pk=pk)
    
    if request.method == 'POST':
        codigo = cohorte.codigo
        cohorte.delete()
        messages.success(request, f'Cohorte {codigo} eliminada correctamente.')
        return redirect('cohorte_list')
    
    return render(request, 'core/cohorte_confirm_delete.html', {
        'cohorte': cohorte
    })


# =============================================================================
# INSCRIPCIONES
# =============================================================================

@login_required
def inscripcion_list(request):
    """Lista de inscripciones"""
    query = request.GET.get('q', '')
    inscripciones = Inscripcion.objects.select_related(
        'estudiante', 'cohorte', 'cohorte__curso'
    )
    
    if query:
        inscripciones = inscripciones.filter(
            Q(estudiante__nombre__icontains=query) |
            Q(estudiante__apellido__icontains=query) |
            Q(cohorte__codigo__icontains=query)
        )
    
    # Filtrar por estudiante si el usuario es estudiante
    if request.user.es_estudiante:
        try:
            inscripciones = inscripciones.filter(estudiante=request.user.estudiante_perfil)
        except Estudiante.DoesNotExist:
            inscripciones = Inscripcion.objects.none()
    
    paginator = Paginator(inscripciones, 15)
    page = request.GET.get('page')
    inscripciones = paginator.get_page(page)
    
    return render(request, 'core/inscripcion_list.html', {
        'inscripciones': inscripciones,
        'query': query
    })


@login_required
@admin_required
def inscripcion_create(request):
    """Crear inscripcion"""
    if request.method == 'POST':
        form = InscripcionForm(request.POST)
        if form.is_valid():
            inscripcion = form.save()
            messages.success(request, 'Inscripcion creada correctamente.')
            return redirect('inscripcion_detail', pk=inscripcion.pk)
    else:
        form = InscripcionForm()
        # Pre-llenar monto con el costo del curso si se selecciona cohorte
        cohorte_id = request.GET.get('cohorte')
        if cohorte_id:
            try:
                cohorte = Cohorte.objects.get(pk=cohorte_id)
                form.initial['cohorte'] = cohorte
                form.initial['monto_acordado'] = cohorte.curso.costo
            except Cohorte.DoesNotExist:
                pass
    
    return render(request, 'core/inscripcion_form.html', {
        'form': form,
        'titulo': 'Nueva Inscripcion'
    })


@login_required
def inscripcion_detail(request, pk):
    """Detalle de inscripcion"""
    inscripcion = get_object_or_404(
        Inscripcion.objects.select_related(
            'estudiante', 'cohorte', 'cohorte__curso', 'cohorte__docente'
        ),
        pk=pk
    )
    
    # Verificar permisos
    if request.user.es_estudiante:
        try:
            if inscripcion.estudiante != request.user.estudiante_perfil:
                messages.error(request, 'No tienes permiso para ver esta inscripcion.')
                return redirect('inscripcion_list')
        except Estudiante.DoesNotExist:
            messages.error(request, 'No tienes permiso para ver esta inscripcion.')
            return redirect('inscripcion_list')
    
    pagos = inscripcion.pagos.order_by('-fecha_pago')
    
    return render(request, 'core/inscripcion_detail.html', {
        'inscripcion': inscripcion,
        'pagos': pagos
    })


@login_required
@admin_required
def inscripcion_update(request, pk):
    """Editar inscripcion"""
    inscripcion = get_object_or_404(Inscripcion, pk=pk)
    
    if request.method == 'POST':
        form = InscripcionForm(request.POST, instance=inscripcion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inscripcion actualizada correctamente.')
            return redirect('inscripcion_detail', pk=pk)
    else:
        form = InscripcionForm(instance=inscripcion)
    
    return render(request, 'core/inscripcion_form.html', {
        'form': form,
        'inscripcion': inscripcion,
        'titulo': f'Editar Inscripcion'
    })


@login_required
@admin_required
def inscripcion_cancelar(request, pk):
    """Cancelar inscripcion"""
    inscripcion = get_object_or_404(Inscripcion, pk=pk)
    
    if request.method == 'POST':
        inscripcion.estado = 'cancelada'
        inscripcion.save()
        messages.success(request, 'Inscripcion cancelada correctamente.')
        return redirect('inscripcion_list')
    
    return render(request, 'core/inscripcion_confirm_cancel.html', {
        'inscripcion': inscripcion
    })


# =============================================================================
# PAGOS ESTUDIANTES
# =============================================================================

@login_required
def pago_estudiante_list(request):
    """Lista de pagos de estudiantes"""
    query = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    pagos = PagoEstudiante.objects.select_related(
        'inscripcion', 'inscripcion__estudiante', 'inscripcion__cohorte'
    )
    
    if query:
        pagos = pagos.filter(
            Q(inscripcion__estudiante__nombre__icontains=query) |
            Q(inscripcion__estudiante__apellido__icontains=query) |
            Q(numero_recibo__icontains=query)
        )
    
    if estado:
        pagos = pagos.filter(estado=estado)
    
    # Filtrar por estudiante si el usuario es estudiante
    if request.user.es_estudiante:
        try:
            pagos = pagos.filter(inscripcion__estudiante=request.user.estudiante_perfil)
        except Estudiante.DoesNotExist:
            pagos = PagoEstudiante.objects.none()
    
    paginator = Paginator(pagos, 15)
    page = request.GET.get('page')
    pagos = paginator.get_page(page)
    
    return render(request, 'core/pago_estudiante_list.html', {
        'pagos': pagos,
        'query': query,
        'estado_filtro': estado,
        'estados': PagoEstudiante.Estado.choices
    })


@login_required
@admin_required
def pago_estudiante_create(request):
    """Registrar pago de estudiante"""
    if request.method == 'POST':
        form = PagoEstudianteForm(request.POST)
        if form.is_valid():
            pago = form.save()
            messages.success(request, 'Pago registrado correctamente.')
            return redirect('pago_estudiante_detail', pk=pago.pk)
    else:
        form = PagoEstudianteForm()
        inscripcion_id = request.GET.get('inscripcion')
        if inscripcion_id:
            try:
                inscripcion = Inscripcion.objects.get(pk=inscripcion_id)
                form.initial['inscripcion'] = inscripcion
                form.initial['monto'] = inscripcion.saldo_pendiente
            except Inscripcion.DoesNotExist:
                pass
    
    return render(request, 'core/pago_estudiante_form.html', {
        'form': form,
        'titulo': 'Registrar Pago'
    })


@login_required
def pago_estudiante_detail(request, pk):
    """Detalle de pago de estudiante"""
    pago = get_object_or_404(
        PagoEstudiante.objects.select_related(
            'inscripcion', 'inscripcion__estudiante', 'inscripcion__cohorte'
        ),
        pk=pk
    )
    
    # Verificar permisos
    if request.user.es_estudiante:
        try:
            if pago.inscripcion.estudiante != request.user.estudiante_perfil:
                messages.error(request, 'No tienes permiso para ver este pago.')
                return redirect('pago_estudiante_list')
        except Estudiante.DoesNotExist:
            messages.error(request, 'No tienes permiso para ver este pago.')
            return redirect('pago_estudiante_list')
    
    return render(request, 'core/pago_estudiante_detail.html', {
        'pago': pago
    })


@login_required
@admin_required
def pago_estudiante_verificar(request, pk):
    """Verificar pago de estudiante"""
    pago = get_object_or_404(PagoEstudiante, pk=pk)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'verificar':
            pago.estado = 'verificado'
            messages.success(request, 'Pago verificado correctamente.')
        elif accion == 'rechazar':
            pago.estado = 'rechazado'
            messages.warning(request, 'Pago rechazado.')
        pago.save()
        return redirect('pago_estudiante_detail', pk=pk)
    
    return render(request, 'core/pago_estudiante_verificar.html', {
        'pago': pago
    })


# =============================================================================
# PAGOS DOCENTES
# =============================================================================

@login_required
def pago_docente_list(request):
    """Lista de pagos a docentes"""
    query = request.GET.get('q', '')
    pagos = PagoDocente.objects.select_related('docente', 'cohorte', 'cohorte__curso')
    
    if query:
        pagos = pagos.filter(
            Q(docente__nombre__icontains=query) |
            Q(docente__apellido__icontains=query) |
            Q(numero_comprobante__icontains=query)
        )
    
    # Filtrar por docente si el usuario es docente
    if request.user.es_docente:
        try:
            pagos = pagos.filter(docente=request.user.docente_perfil)
        except Docente.DoesNotExist:
            pagos = PagoDocente.objects.none()
    
    paginator = Paginator(pagos, 15)
    page = request.GET.get('page')
    pagos = paginator.get_page(page)
    
    return render(request, 'core/pago_docente_list.html', {
        'pagos': pagos,
        'query': query
    })


@login_required
@admin_required
def pago_docente_create(request):
    """Registrar pago a docente"""
    if request.method == 'POST':
        form = PagoDocenteForm(request.POST)
        if form.is_valid():
            pago = form.save()
            messages.success(request, 'Pago a docente registrado correctamente.')
            return redirect('pago_docente_detail', pk=pago.pk)
    else:
        form = PagoDocenteForm()
    
    return render(request, 'core/pago_docente_form.html', {
        'form': form,
        'titulo': 'Registrar Pago a Docente'
    })


@login_required
def pago_docente_detail(request, pk):
    """Detalle de pago a docente"""
    pago = get_object_or_404(
        PagoDocente.objects.select_related('docente', 'cohorte', 'cohorte__curso'),
        pk=pk
    )
    
    # Verificar permisos
    if request.user.es_docente:
        try:
            if pago.docente != request.user.docente_perfil:
                messages.error(request, 'No tienes permiso para ver este pago.')
                return redirect('pago_docente_list')
        except Docente.DoesNotExist:
            messages.error(request, 'No tienes permiso para ver este pago.')
            return redirect('pago_docente_list')
    
    return render(request, 'core/pago_docente_detail.html', {
        'pago': pago
    })


# =============================================================================
# SESIONES Y ASISTENCIA
# =============================================================================

@login_required
def sesion_list(request, cohorte_pk):
    """Lista de sesiones de una cohorte"""
    cohorte = get_object_or_404(Cohorte.objects.select_related('curso', 'docente'), pk=cohorte_pk)
    
    # Verificar permisos para docentes
    if request.user.es_docente:
        try:
            if cohorte.docente != request.user.docente_perfil:
                messages.error(request, 'No tienes permiso para ver estas sesiones.')
                return redirect('cohorte_list')
        except Docente.DoesNotExist:
            messages.error(request, 'No tienes permiso para ver estas sesiones.')
            return redirect('cohorte_list')
    
    sesiones = cohorte.sesiones.order_by('numero_sesion')
    
    return render(request, 'core/sesion_list.html', {
        'cohorte': cohorte,
        'sesiones': sesiones
    })


@login_required
def sesion_create(request, cohorte_pk):
    """Crear sesion"""
    cohorte = get_object_or_404(Cohorte, pk=cohorte_pk)
    
    # Verificar permisos
    if not request.user.es_admin:
        if request.user.es_docente:
            try:
                if cohorte.docente != request.user.docente_perfil:
                    messages.error(request, 'No tienes permiso para crear sesiones en esta cohorte.')
                    return redirect('cohorte_list')
            except Docente.DoesNotExist:
                messages.error(request, 'No tienes permiso para crear sesiones.')
                return redirect('cohorte_list')
        else:
            messages.error(request, 'No tienes permiso para crear sesiones.')
            return redirect('cohorte_list')
    
    if request.method == 'POST':
        form = SesionForm(request.POST)
        if form.is_valid():
            sesion = form.save(commit=False)
            sesion.cohorte = cohorte
            sesion.save()
            messages.success(request, f'Sesion {sesion.numero_sesion} creada correctamente.')
            return redirect('sesion_list', cohorte_pk=cohorte_pk)
    else:
        # Sugerir siguiente numero de sesion
        ultima_sesion = cohorte.sesiones.order_by('-numero_sesion').first()
        siguiente_numero = (ultima_sesion.numero_sesion + 1) if ultima_sesion else 1
        form = SesionForm(initial={'numero_sesion': siguiente_numero})
    
    return render(request, 'core/sesion_form.html', {
        'form': form,
        'cohorte': cohorte,
        'titulo': 'Nueva Sesion'
    })


@login_required
def asistencia_registrar(request, pk):
    """Registrar asistencia de una sesion"""
    sesion = get_object_or_404(
        Sesion.objects.select_related('cohorte', 'cohorte__curso', 'cohorte__docente'),
        pk=pk
    )
    
    # Verificar permisos
    if not request.user.es_admin:
        if request.user.es_docente:
            try:
                if sesion.cohorte.docente != request.user.docente_perfil:
                    messages.error(request, 'No tienes permiso para registrar asistencia.')
                    return redirect('cohorte_list')
            except Docente.DoesNotExist:
                messages.error(request, 'No tienes permiso para registrar asistencia.')
                return redirect('cohorte_list')
        else:
            messages.error(request, 'No tienes permiso para registrar asistencia.')
            return redirect('cohorte_list')
    
    # Obtener estudiantes inscritos
    inscripciones = sesion.cohorte.inscripciones.filter(
        estado='activa'
    ).select_related('estudiante')
    
    # Obtener asistencias existentes
    asistencias_existentes = {
        a.estudiante_id: a for a in sesion.asistencias.all()
    }
    
    estudiantes_asistencia = []
    for inscripcion in inscripciones:
        estudiante = inscripcion.estudiante
        asistencia = asistencias_existentes.get(estudiante.id)
        estudiantes_asistencia.append({
            'estudiante': estudiante,
            'asistencia': asistencia,
            'estado': asistencia.estado if asistencia else 'ausente'
        })
    
    return render(request, 'core/asistencia_registrar.html', {
        'sesion': sesion,
        'estudiantes_asistencia': estudiantes_asistencia,
        'estados': Asistencia.Estado.choices
    })


@login_required
@require_POST
def api_guardar_asistencia(request):
    """API para guardar asistencia via AJAX"""
    try:
        data = json.loads(request.body)
        sesion_id = data.get('sesion_id')
        asistencias_data = data.get('asistencias', [])
        
        sesion = get_object_or_404(Sesion, pk=sesion_id)
        
        # Verificar permisos
        if not request.user.es_admin:
            if request.user.es_docente:
                try:
                    if sesion.cohorte.docente != request.user.docente_perfil:
                        return JsonResponse({'error': 'Sin permiso'}, status=403)
                except Docente.DoesNotExist:
                    return JsonResponse({'error': 'Sin permiso'}, status=403)
            else:
                return JsonResponse({'error': 'Sin permiso'}, status=403)
        
        for item in asistencias_data:
            estudiante_id = item.get('estudiante_id')
            estado = item.get('estado')
            observaciones = item.get('observaciones', '')
            
            Asistencia.objects.update_or_create(
                sesion=sesion,
                estudiante_id=estudiante_id,
                defaults={
                    'estado': estado,
                    'observaciones': observaciones
                }
            )
        
        return JsonResponse({'success': True, 'message': 'Asistencia guardada correctamente'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# =============================================================================
# REPORTES
# =============================================================================

@login_required
@admin_required
def reportes_dashboard(request):
    """Dashboard de reportes"""
    return render(request, 'core/reportes_dashboard.html')


@login_required
@admin_required
def reporte_ingresos(request):
    """Reporte de ingresos"""
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    pagos = PagoEstudiante.objects.filter(estado='verificado')
    
    if fecha_inicio:
        pagos = pagos.filter(fecha_pago__gte=fecha_inicio)
    if fecha_fin:
        pagos = pagos.filter(fecha_pago__lte=fecha_fin)
    
    pagos = pagos.select_related(
        'inscripcion', 'inscripcion__estudiante', 
        'inscripcion__cohorte', 'inscripcion__cohorte__curso'
    ).order_by('-fecha_pago')
    
    total = pagos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    # Resumen por metodo de pago
    por_metodo = pagos.values('metodo_pago').annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    )
    
    # Resumen por curso
    por_curso = pagos.values(
        'inscripcion__cohorte__curso__nombre'
    ).annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    ).order_by('-total')
    
    return render(request, 'core/reporte_ingresos.html', {
        'pagos': pagos[:100],
        'total': total,
        'por_metodo': por_metodo,
        'por_curso': por_curso,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    })


@login_required
@admin_required
def reporte_pagos_docentes(request):
    """Reporte de pagos a docentes"""
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    pagos = PagoDocente.objects.all()
    
    if fecha_inicio:
        pagos = pagos.filter(fecha_pago__gte=fecha_inicio)
    if fecha_fin:
        pagos = pagos.filter(fecha_pago__lte=fecha_fin)
    
    pagos = pagos.select_related(
        'docente', 'cohorte', 'cohorte__curso'
    ).order_by('-fecha_pago')
    
    total_pagado = pagos.filter(estado='pagado').aggregate(
        total=Sum('monto')
    )['total'] or Decimal('0.00')
    
    total_pendiente = pagos.filter(estado='pendiente').aggregate(
        total=Sum('monto')
    )['total'] or Decimal('0.00')
    
    # Resumen por docente
    por_docente = pagos.filter(estado='pagado').values(
        'docente__nombre', 'docente__apellido'
    ).annotate(
        total=Sum('monto'),
        horas=Sum('horas_trabajadas')
    ).order_by('-total')
    
    return render(request, 'core/reporte_pagos_docentes.html', {
        'pagos': pagos[:100],
        'total_pagado': total_pagado,
        'total_pendiente': total_pendiente,
        'por_docente': por_docente,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    })


@login_required
def reporte_asistencia(request):
    """Reporte de asistencia"""
    cohorte_id = request.GET.get('cohorte')
    
    cohortes = Cohorte.objects.select_related('curso')
    
    # Filtrar cohortes para docentes
    if request.user.es_docente:
        try:
            cohortes = cohortes.filter(docente=request.user.docente_perfil)
        except Docente.DoesNotExist:
            cohortes = Cohorte.objects.none()
    
    cohorte = None
    estudiantes_asistencia = []
    
    if cohorte_id:
        cohorte = get_object_or_404(Cohorte.objects.select_related('curso', 'docente'), pk=cohorte_id)
        
        # Verificar permisos
        if request.user.es_docente:
            try:
                if cohorte.docente != request.user.docente_perfil:
                    messages.error(request, 'No tienes permiso para ver este reporte.')
                    return redirect('reportes_dashboard')
            except Docente.DoesNotExist:
                messages.error(request, 'No tienes permiso para ver este reporte.')
                return redirect('reportes_dashboard')
        
        inscripciones = cohorte.inscripciones.filter(estado='activa').select_related('estudiante')
        total_sesiones = cohorte.sesiones.count()
        
        for inscripcion in inscripciones:
            estudiante = inscripcion.estudiante
            asistencias = Asistencia.objects.filter(
                sesion__cohorte=cohorte,
                estudiante=estudiante
            )
            presentes = asistencias.filter(estado='presente').count()
            tardanzas = asistencias.filter(estado='tardanza').count()
            ausentes = asistencias.filter(estado='ausente').count()
            justificados = asistencias.filter(estado='justificado').count()
            
            porcentaje = 0
            if total_sesiones > 0:
                porcentaje = ((presentes + tardanzas + justificados) / total_sesiones) * 100
            
            estudiantes_asistencia.append({
                'estudiante': estudiante,
                'presentes': presentes,
                'tardanzas': tardanzas,
                'ausentes': ausentes,
                'justificados': justificados,
                'porcentaje': round(porcentaje, 1)
            })
    
    return render(request, 'core/reporte_asistencia.html', {
        'cohortes': cohortes,
        'cohorte_seleccionada': cohorte,
        'estudiantes_asistencia': estudiantes_asistencia
    })
