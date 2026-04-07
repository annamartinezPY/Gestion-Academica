import re
from django import forms
from .models import Modalidad, Curso, Cohorte, Rol


METODOS_PAGO = [
    ('efectivo', 'Efectivo'),
    ('transferencia', 'Transferencia'),
    ('tarjeta', 'Tarjeta'),
]

TIPOS_PAGO_DOCENTE = [
    ('horas', 'Por horas dictadas'),
    ('materiales', 'Por materiales'),
]


class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'usuario@email.com', 'autofocus': True})
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )


class UsuarioForm(forms.Form):
    nombre = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        required=False,
        label='Contraseña (vacío = sin cambio)',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    rol = forms.ModelChoiceField(
        queryset=Rol.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='— Seleccione rol —'
    )


class DocenteForm(forms.Form):
    nombre = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        required=False,
        label='Contraseña (vacío = sin cambio en edición)',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    especialidad = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Programación Web'})
    )
    tarifa_hora = forms.FloatField(
        min_value=0,
        initial=0,
        label='Tarifa por hora ($)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )


class EstudianteForm(forms.Form):
    nombre = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        required=False,
        label='Contraseña (vacío = sin cambio en edición)',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    documento = forms.CharField(
        required=False,
        label='Documento (CI / Pasaporte)',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    telefono = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class CursoForm(forms.Form):
    nombre = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    modalidad = forms.ModelChoiceField(
        queryset=Modalidad.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='— Seleccione modalidad —'
    )
    horas_totales = forms.IntegerField(
        min_value=0, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    tarifa_estudiante = forms.FloatField(
        min_value=0, initial=0,
        label='Tarifa para estudiantes ($)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    condiciones_ingreso = forms.CharField(
        required=False,
        label='Condiciones de inscripción',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                     'placeholder': 'Ej: Secundario completo. Edad mínima 18 años.'})
    )


def validar_fecha(valor):
    if valor and not re.match(r'^\d{4}-\d{2}-\d{2}$', valor):
        raise forms.ValidationError('Formato inválido. Use YYYY-MM-DD.')
    return valor


class CohorteForm(forms.Form):
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 2025-A'})
    )
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.filter(activo=1),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='— Seleccione curso —'
    )
    fecha_inicio = forms.CharField(
        label='Fecha inicio (YYYY-MM-DD)',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    fecha_fin = forms.CharField(
        label='Fecha fin (YYYY-MM-DD)',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    cupo_maximo = forms.IntegerField(
        min_value=1, initial=30,
        label='Cupo máximo',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def clean_fecha_inicio(self):
        return validar_fecha(self.cleaned_data.get('fecha_inicio'))

    def clean_fecha_fin(self):
        return validar_fecha(self.cleaned_data.get('fecha_fin'))


class SesionForm(forms.Form):
    fecha = forms.CharField(
        label='Fecha (YYYY-MM-DD)',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    hora_inicio = forms.CharField(
        label='Hora inicio (HH:MM)',
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    hora_fin = forms.CharField(
        label='Hora fin (HH:MM)',
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    tema = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tema de la clase'})
    )

    def clean_fecha(self):
        return validar_fecha(self.cleaned_data.get('fecha'))


class InscripcionForm(forms.Form):
    estudiante_id = forms.IntegerField(widget=forms.HiddenInput())
    cohorte_id = forms.IntegerField(widget=forms.HiddenInput())


class PagoEstudianteForm(forms.Form):
    inscripcion_id = forms.IntegerField(widget=forms.HiddenInput())
    monto = forms.FloatField(
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    metodo_pago = forms.ChoiceField(
        choices=METODOS_PAGO,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    observacion = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class PagoDocenteHorasForm(forms.Form):
    docente_id = forms.IntegerField(widget=forms.HiddenInput())
    cohorte_id = forms.IntegerField(widget=forms.HiddenInput())
    horas_dictadas = forms.FloatField(
        min_value=0.1,
        label='Horas dictadas',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'})
    )
    observacion = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class PagoDocenteMaterialesForm(forms.Form):
    docente_id = forms.IntegerField(widget=forms.HiddenInput())
    cohorte_id = forms.IntegerField(widget=forms.HiddenInput())
    concepto = forms.CharField(
        label='Concepto / descripción del material',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    monto = forms.FloatField(
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    observacion = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )