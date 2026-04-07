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


def logout_view(request):
    request.session.flush()
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('login')