import uuid
import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from ..decorators import hash_password
from ..models import Usuario, PasswordResetToken


def _token_valido(token_obj):
    """Retorna True si el token no fue usado y no expiró."""
    if token_obj.usado:
        return False
    try:
        expira = datetime.datetime.fromisoformat(token_obj.expira)
        return datetime.datetime.now() < expira
    except (ValueError, TypeError):
        return False


def solicitar_reset(request):
    """Paso 1: el usuario ingresa su email y recibe el link por correo."""
    if request.session.get('usuario_id'):
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        # Siempre mostramos el mismo mensaje para no revelar si el email existe
        try:
            usuario = Usuario.objects.get(email__iexact=email, activo=1)
            _enviar_link(request, usuario)
        except Usuario.DoesNotExist:
            pass
        messages.success(
            request,
            'Si el correo existe en el sistema, recibirás un enlace para restablecer tu contraseña.'
        )
        return redirect('password_reset_solicitar')

    return render(request, 'auth/password_reset_solicitar.html')


def _enviar_link(request, usuario):
    """Genera un token y envía el email con el link de recuperación."""
    horas = getattr(settings, 'PASSWORD_RESET_EXPIRE_HOURS', 2)
    token_str = uuid.uuid4().hex
    expira = (datetime.datetime.now() + datetime.timedelta(hours=horas)).isoformat()

    # Invalida tokens anteriores del mismo usuario
    PasswordResetToken.objects.filter(usuario=usuario, usado=0).update(usado=1)

    PasswordResetToken.objects.create(
        usuario=usuario,
        token=token_str,
        expira=expira,
        usado=0,
    )

    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    link = f"{site_url}/reset-password/{token_str}/"
    nombre = f"{usuario.nombre} {usuario.apellido}"

    cuerpo = (
        f"Hola {nombre},\n\n"
        f"Recibimos una solicitud para restablecer la contraseña de tu cuenta.\n\n"
        f"Hacé clic en el siguiente enlace (válido por {horas} hora(s)):\n"
        f"{link}\n\n"
        f"Si no solicitaste este cambio, podés ignorar este mensaje.\n\n"
        f"— Equipo de Gestión Académica"
    )

    send_mail(
        subject='Restablecer contraseña — Gestión Académica',
        message=cuerpo,
        from_email=getattr(settings, 'EMAIL_FROM', 'no-reply@gestionacademica.edu'),
        recipient_list=[usuario.email],
        fail_silently=True,
    )


def nueva_contrasena(request, token):
    """Paso 2: el usuario abre el link y establece una nueva contraseña."""
    if request.session.get('usuario_id'):
        return redirect('dashboard')

    try:
        token_obj = PasswordResetToken.objects.select_related('usuario').get(token=token)
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'El enlace no es válido.')
        return redirect('login')

    if not _token_valido(token_obj):
        messages.error(request, 'El enlace expiró o ya fue utilizado. Solicitá uno nuevo.')
        return redirect('password_reset_solicitar')

    if request.method == 'POST':
        nueva = request.POST.get('password', '').strip()
        confirmar = request.POST.get('password_confirm', '').strip()

        if len(nueva) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
        elif nueva != confirmar:
            messages.error(request, 'Las contraseñas no coinciden.')
        else:
            usuario = token_obj.usuario
            usuario.password = hash_password(nueva)
            usuario.save()
            token_obj.usado = 1
            token_obj.save()
            messages.success(request, 'Contraseña actualizada. Ya podés iniciar sesión.')
            return redirect('login')

    return render(request, 'auth/password_reset_nueva.html', {'token': token})
