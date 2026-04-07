"""
Decoradores personalizados para control de acceso
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """Decorador que requiere rol de administrador"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.es_admin:
            messages.error(request, 'No tienes permiso para acceder a esta seccion.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def docente_required(view_func):
    """Decorador que requiere rol de docente o admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.es_admin or request.user.es_docente):
            messages.error(request, 'No tienes permiso para acceder a esta seccion.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def estudiante_required(view_func):
    """Decorador que requiere rol de estudiante o admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.es_admin or request.user.es_estudiante):
            messages.error(request, 'No tienes permiso para acceder a esta seccion.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
