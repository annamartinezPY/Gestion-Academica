"""
Formularios Django para el Sistema de Gestion Academica
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .models import (
    Usuario, Estudiante, Docente, Curso, Cohorte,
    Inscripcion, PagoEstudiante, PagoDocente, Sesion
)


class LoginForm(AuthenticationForm):
    """Formulario de login personalizado"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuario',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contrasena'
        })
    )


class CambiarPasswordForm(PasswordChangeForm):
    """Formulario para cambiar contrasena"""
    old_password = forms.CharField(
        label='Contrasena Actual',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label='Nueva Contrasena',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label='Confirmar Nueva Contrasena',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


class UsuarioForm(forms.ModelForm):
    """Formulario para Usuario"""
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Dejar vacio para mantener la contrasena actual'
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'rol', 'telefono', 'direccion', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EstudianteForm(forms.ModelForm):
    """Formulario para Estudiante"""
    class Meta:
        model = Estudiante
        fields = ['cedula', 'nombre', 'apellido', 'email', 'telefono', 'direccion', 'fecha_nacimiento', 'activo']
        widgets = {
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DocenteForm(forms.ModelForm):
    """Formulario para Docente"""
    class Meta:
        model = Docente
        fields = ['cedula', 'nombre', 'apellido', 'email', 'telefono', 'especialidad', 'tarifa_hora', 'activo']
        widgets = {
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'especialidad': forms.TextInput(attrs={'class': 'form-control'}),
            'tarifa_hora': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CursoForm(forms.ModelForm):
    """Formulario para Curso"""
    class Meta:
        model = Curso
        fields = ['codigo', 'nombre', 'descripcion', 'modalidad', 'duracion_horas', 'costo', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'modalidad': forms.Select(attrs={'class': 'form-select'}),
            'duracion_horas': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CohorteForm(forms.ModelForm):
    """Formulario para Cohorte"""
    class Meta:
        model = Cohorte
        fields = ['curso', 'docente', 'codigo', 'fecha_inicio', 'fecha_fin', 'horario', 'cupo_maximo', 'estado', 'aula']
        widgets = {
            'curso': forms.Select(attrs={'class': 'form-select'}),
            'docente': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'horario': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Lunes y Miercoles 18:00-21:00'}),
            'cupo_maximo': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'aula': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['curso'].queryset = Curso.objects.filter(activo=True)
        self.fields['docente'].queryset = Docente.objects.filter(activo=True)
        self.fields['docente'].required = False


class InscripcionForm(forms.ModelForm):
    """Formulario para Inscripcion"""
    class Meta:
        model = Inscripcion
        fields = ['estudiante', 'cohorte', 'monto_acordado', 'observaciones']
        widgets = {
            'estudiante': forms.Select(attrs={'class': 'form-select'}),
            'cohorte': forms.Select(attrs={'class': 'form-select'}),
            'monto_acordado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estudiante'].queryset = Estudiante.objects.filter(activo=True)
        self.fields['cohorte'].queryset = Cohorte.objects.exclude(estado='cancelado')


class PagoEstudianteForm(forms.ModelForm):
    """Formulario para Pago de Estudiante"""
    class Meta:
        model = PagoEstudiante
        fields = ['inscripcion', 'monto', 'fecha_pago', 'metodo_pago', 'numero_recibo', 'observaciones']
        widgets = {
            'inscripcion': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_pago': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
            'numero_recibo': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inscripcion'].queryset = Inscripcion.objects.filter(estado='activa')


class PagoDocenteForm(forms.ModelForm):
    """Formulario para Pago a Docente"""
    class Meta:
        model = PagoDocente
        fields = ['docente', 'cohorte', 'monto', 'horas_trabajadas', 'fecha_pago', 'metodo_pago', 'numero_comprobante', 'observaciones']
        widgets = {
            'docente': forms.Select(attrs={'class': 'form-select'}),
            'cohorte': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'horas_trabajadas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_pago': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
            'numero_comprobante': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['docente'].queryset = Docente.objects.filter(activo=True)
        self.fields['cohorte'].queryset = Cohorte.objects.all()


class SesionForm(forms.ModelForm):
    """Formulario para Sesion"""
    class Meta:
        model = Sesion
        fields = ['numero_sesion', 'fecha', 'hora_inicio', 'hora_fin', 'tema', 'observaciones']
        widgets = {
            'numero_sesion': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'tema': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
