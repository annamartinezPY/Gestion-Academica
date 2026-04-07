import hashlib
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def login_required(f):
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            messages.warning(request, 'Debe iniciar sesión para continuar.')
            return redirect('login')
        return f(request, *args, **kwargs)
    return wrapper


def rol_required(*roles):
    """Decorator que restringe el acceso a ciertos roles."""
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.session.get('rol') not in roles:
                messages.error(request, 'No tiene permisos para acceder a esta sección.')
                return redirect('dashboard')
            return f(request, *args, **kwargs)
        return wrapper
    return decorator


def get_usuario_sesion(request):
    """Retorna un dict con los datos del usuario en sesión."""
    return {
        'id': request.session.get('usuario_id'),
        'nombre': request.session.get('nombre'),
        'apellido': request.session.get('apellido'),
        'email': request.session.get('email'),
        'rol': request.session.get('rol'),
        'perfil_id': request.session.get('perfil_id'),  # docente_id o estudiante_id
    }
