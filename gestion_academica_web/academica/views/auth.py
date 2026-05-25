from django.shortcuts import render, redirect
from django.contrib import messages
from ..models import Usuario, Docente, Estudiante
from ..decorators import hash_password
from ..forms import LoginForm


def login_view(request):
    if 'usuario_id' in request.session:
        return redirect('dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = hash_password(form.cleaned_data['password'])
        try:
            usuario = Usuario.objects.select_related('rol').get(
                email=email, password=password, activo=1
            )

            # Si el usuario debe cambiar la contraseña, lo dirigimos al flujo
            # de cambio forzado antes de crear la sesión completa.
            if usuario.must_change_password:
                request.session['pending_pwd_change_user'] = usuario.id
                messages.info(
                    request,
                    'Por seguridad, debés cambiar tu contraseña antes de continuar.'
                )
                return redirect('password_cambio_forzado')

            request.session['usuario_id'] = usuario.id
            request.session['nombre'] = usuario.nombre
            request.session['apellido'] = usuario.apellido
            request.session['email'] = usuario.email
            request.session['rol'] = usuario.rol.nombre

            # Guardar perfil_id según rol
            if usuario.rol.nombre == 'docente':
                try:
                    request.session['perfil_id'] = usuario.docente.id
                except Docente.DoesNotExist:
                    request.session['perfil_id'] = None
            elif usuario.rol.nombre == 'estudiante':
                try:
                    request.session['perfil_id'] = usuario.estudiante.id
                except Estudiante.DoesNotExist:
                    request.session['perfil_id'] = None
            else:
                request.session['perfil_id'] = None

            messages.success(request, f'Bienvenido/a, {usuario.nombre} {usuario.apellido}.')
            return redirect('dashboard')
        except Usuario.DoesNotExist:
            messages.error(request, 'Credenciales incorrectas o usuario inactivo.')

    return render(request, 'login.html', {'form': form})


def cambio_password_forzado(request):
    """Flujo obligatorio de cambio de contraseña en el primer inicio de sesión.
    Solo accesible si en la sesión hay un 'pending_pwd_change_user' (no hay sesión
    activa todavía)."""
    pending_id = request.session.get('pending_pwd_change_user')
    if not pending_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.select_related('rol').get(pk=pending_id, activo=1)
    except Usuario.DoesNotExist:
        request.session.pop('pending_pwd_change_user', None)
        messages.error(request, 'Usuario no encontrado.')
        return redirect('login')

    if request.method == 'POST':
        nueva = (request.POST.get('password') or '').strip()
        confirmar = (request.POST.get('password_confirm') or '').strip()

        if len(nueva) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
        elif nueva != confirmar:
            messages.error(request, 'Las contraseñas no coinciden.')
        elif hash_password(nueva) == usuario.password:
            messages.error(request, 'La nueva contraseña debe ser distinta a la actual.')
        else:
            usuario.password = hash_password(nueva)
            usuario.must_change_password = 0
            usuario.save()

            # Login efectivo
            request.session.pop('pending_pwd_change_user', None)
            request.session['usuario_id'] = usuario.id
            request.session['nombre'] = usuario.nombre
            request.session['apellido'] = usuario.apellido
            request.session['email'] = usuario.email
            request.session['rol'] = usuario.rol.nombre
            if usuario.rol.nombre == 'docente':
                try:
                    request.session['perfil_id'] = usuario.docente.id
                except Docente.DoesNotExist:
                    request.session['perfil_id'] = None
            elif usuario.rol.nombre == 'estudiante':
                try:
                    request.session['perfil_id'] = usuario.estudiante.id
                except Estudiante.DoesNotExist:
                    request.session['perfil_id'] = None
            else:
                request.session['perfil_id'] = None

            messages.success(
                request,
                f'Contraseña actualizada. Bienvenido/a, {usuario.nombre} {usuario.apellido}.'
            )
            return redirect('dashboard')

    return render(request, 'auth/cambio_password_forzado.html', {'usuario': usuario})


def logout_view(request):
    request.session.flush()
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('login')