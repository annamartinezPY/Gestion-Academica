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


def permiso_required(clave):
    """
    Decorator que verifica que el usuario tenga un permiso específico por su rol.
    Uso: @permiso_required('pagos.aprobar')
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(request, *args, **kwargs):
            rol = request.session.get('rol')
            # Admin siempre tiene todos los permisos
            if rol == 'admin':
                return f(request, *args, **kwargs)
            if not _tiene_permiso(rol, clave):
                messages.error(request, 'No tiene permiso para realizar esta acción.')
                return redirect('dashboard')
            return f(request, *args, **kwargs)
        return wrapper
    return decorator


def _tiene_permiso(rol_nombre, clave):
    """Consulta si el rol tiene la clave de permiso indicada."""
    try:
        from .models import RolPermiso, Permiso, Rol
        rol = Rol.objects.get(nombre=rol_nombre)
        return RolPermiso.objects.filter(
            rol=rol, permiso__clave=clave
        ).exists()
    except Exception:
        return False


def tiene_permiso_ctx(rol_nombre, clave):
    """Versión no-decorator para usar en templates/vistas: retorna bool."""
    if not rol_nombre:
        return False
    return rol_nombre == 'admin' or _tiene_permiso(rol_nombre, clave)


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
