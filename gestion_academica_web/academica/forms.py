import re
from django import forms
from .models import Modalidad, Curso, Cohorte, Rol, Institucion, NivelEducativo, TipoContratacion, CondicionInscripcion

DIAS_SEMANA = [
    ('Lunes', 'Lunes'), ('Martes', 'Martes'), ('Miércoles', 'Miércoles'),
    ('Jueves', 'Jueves'), ('Viernes', 'Viernes'),
    ('Sábado', 'Sábado'), ('Domingo', 'Domingo'),
]


EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
TELEFONO_RE = re.compile(r'^\d+$')
NOMBRE_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s'-]+$")
DOCUMENTO_RE = re.compile(r'^\d+$')
CIUDAD_RE = re.compile(r'^[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ\s.\-]+$')


def validar_nombre(valor, campo='nombre'):
    valor = (valor or '').strip()
    if valor and not NOMBRE_RE.match(valor):
        raise forms.ValidationError(
            f'El {campo} sólo puede contener letras.'
        )
    return valor


def validar_email(valor):
    valor = (valor or '').strip()
    if valor and ('@' not in valor or '.' not in valor):
        raise forms.ValidationError(
            'El email debe contener "@" y "." (Ej: usuario@dominio.com).'
        )
    return valor


def validar_telefono(valor):
    valor = (valor or '').strip()
    if valor:
        if not TELEFONO_RE.match(valor):
            raise forms.ValidationError(
                'El teléfono debe contener sólo números, sin caracteres especiales.'
            )
        if len(valor) < 10:
            raise forms.ValidationError(
                'El teléfono debe tener al menos 10 dígitos.'
            )
    return valor


def validar_documento(valor, campo='documento'):
    valor = (valor or '').strip()
    if valor and not DOCUMENTO_RE.match(valor):
        raise forms.ValidationError(
            f'El {campo} debe contener sólo números, sin caracteres especiales.'
        )
    return valor


def validar_direccion(valor):
    # La dirección acepta letras, números y caracteres especiales — sin restricción.
    return (valor or '').strip()


def validar_fecha_nacimiento(valor):
    valor = (valor or '').strip()
    if not valor:
        return valor
    import re as _re
    if not _re.match(r'^\d{4}-\d{2}-\d{2}$', valor):
        raise forms.ValidationError('Formato inválido. Use AAAA-MM-DD.')
    try:
        import datetime
        fn = datetime.date.fromisoformat(valor)
        if fn > datetime.date.today():
            raise forms.ValidationError(
                'La fecha de nacimiento no puede ser mayor al año actual.'
            )
    except ValueError:
        raise forms.ValidationError('Fecha inválida.')
    return valor


def validar_ciudad(valor):
    if valor and not CIUDAD_RE.match(valor):
        raise forms.ValidationError(
            'La ciudad solo admite letras, números, espacios, puntos y guiones.'
        )
    return valor


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
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    cedula = forms.CharField(
        required=False,
        max_length=20,
        label='Cédula de identidad',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Ej: 4123456',
            'inputmode': 'numeric', 'pattern': r'\d+',
        })
    )
    ruc = forms.CharField(
        required=False,
        max_length=20,
        label='RUC',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Ej: 4123456-7',
            'pattern': r'[0-9\-]+',
        })
    )
    telefono = forms.CharField(
        required=False,
        max_length=20,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Solo números',
            'inputmode': 'numeric', 'pattern': r'\d+',
        })
    )
    forzar_cambio_password = forms.BooleanField(
        required=False,
        initial=True,
        label='El usuario debe cambiar la contraseña en el primer inicio de sesión',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # ── Perfil profesional (lo que ve el estudiante) ───────────────────────
    foto = forms.FileField(
        required=False,
        label='Foto de perfil',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/png,image/jpeg,image/jpg,image/webp',
        })
    )
    biografia = forms.CharField(
        required=False,
        label='Biografía',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 4,
            'placeholder': 'Párrafo corto sobre el docente, su enfoque y motivación.',
        })
    )
    areas_experiencia = forms.CharField(
        required=False,
        label='Áreas de experiencia',
        help_text='Separadas por coma. Ej: Node.js, C#, UI/UX',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Node.js, C#, UI/UX',
        })
    )
    trayectoria_academica = forms.CharField(
        required=False,
        label='Trayectoria académica',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 4,
            'placeholder': 'Títulos, certificaciones y trayectoria profesional. Una línea por ítem.',
        })
    )
    linkedin_url = forms.URLField(
        required=False,
        label='LinkedIn',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.linkedin.com/in/usuario',
        })
    )
    otras_redes = forms.CharField(
        required=False,
        label='Otras redes / portafolio',
        help_text='Una por línea, formato: "Etiqueta|https://url". Ej: GitHub|https://github.com/usuario',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3,
            'placeholder': 'GitHub|https://github.com/usuario\nPortfolio|https://miweb.com',
        })
    )

    def clean_foto(self):
        f = self.cleaned_data.get('foto')
        if f and hasattr(f, 'size'):
            if f.size > 5 * 1024 * 1024:
                raise forms.ValidationError('La foto no debe superar los 5 MB.')
            ext = (f.name.rsplit('.', 1)[-1] or '').lower()
            if ext not in ('png', 'jpg', 'jpeg', 'webp'):
                raise forms.ValidationError('Formato no soportado. Usá PNG, JPG o WEBP.')
        return f
    especialidad = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Programación Web'})
    )
    nivel_educativo = forms.ModelChoiceField(
        queryset=NivelEducativo.objects.filter(activo=1).order_by('nombre'),
        required=False,
        label='Nivel educativo',
        empty_label='— Sin asignar —',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    legajo_interno = forms.CharField(
        required=False,
        max_length=50,
        label='Legajo interno',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Se asigna automáticamente',
            'readonly': 'readonly',
        })
    )
    tipo_contratacion = forms.ModelChoiceField(
        queryset=TipoContratacion.objects.filter(activo=1).order_by('nombre'),
        required=False,
        label='Tipo de contratación',
        empty_label='— Sin asignar —',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tarifa_hora = forms.CharField(
        required=False,
        label='Tarifa por hora (₲)',
        widget=forms.TextInput(attrs={
            'class': 'form-control money-gs',
            'inputmode': 'numeric',
            'placeholder': '0',
            'autocomplete': 'off',
        })
    )

    def clean_tarifa_hora(self):
        v = (self.cleaned_data.get('tarifa_hora') or '').strip()
        if not v:
            return 0.0
        # Eliminar separadores (puntos, comas, espacios)
        limpio = v.replace('.', '').replace(',', '').replace(' ', '')
        if not limpio.isdigit():
            raise forms.ValidationError('La tarifa debe ser un número entero en guaraníes.')
        return float(limpio)

    def clean_nombre(self):
        return validar_nombre(self.cleaned_data.get('nombre'), 'nombre')

    def clean_apellido(self):
        return validar_nombre(self.cleaned_data.get('apellido'), 'apellido')

    def clean_email(self):
        return validar_email(self.cleaned_data.get('email', ''))

    def clean_telefono(self):
        return validar_telefono(self.cleaned_data.get('telefono'))

    def clean_cedula(self):
        return validar_documento(self.cleaned_data.get('cedula'), 'cédula')

    def clean_ruc(self):
        v = (self.cleaned_data.get('ruc') or '').strip()
        if v and not re.match(r'^[0-9\-]+$', v):
            raise forms.ValidationError('El RUC admite solo números y guion medio (-).')
        return v


class EstudianteForm(forms.Form):
    nombre = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        required=False,
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    documento = forms.CharField(
        required=False,
        label='Documento (CI / Pasaporte)',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    telefono = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Solo números, sin guiones',
            'data-validate': 'phone',
            'inputmode': 'numeric',
        })
    )
    fecha_nacimiento = forms.CharField(
        required=False,
        label='Fecha de nacimiento',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    direccion_residencia = forms.CharField(
        required=False,
        max_length=255,
        label='Dirección de residencia',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Av. Mariscal López 1234, Asunción',
        })
    )

    def clean_nombre(self):
        return validar_nombre(self.cleaned_data.get('nombre'), 'nombre')

    def clean_apellido(self):
        return validar_nombre(self.cleaned_data.get('apellido'), 'apellido')

    def clean_email(self):
        return validar_email(self.cleaned_data.get('email', ''))

    def clean_telefono(self):
        return validar_telefono(self.cleaned_data.get('telefono'))

    def clean_documento(self):
        return validar_documento(self.cleaned_data.get('documento'), 'documento')

    def clean_direccion_residencia(self):
        return validar_direccion(self.cleaned_data.get('direccion_residencia'))

    def clean_fecha_nacimiento(self):
        return validar_fecha_nacimiento(self.cleaned_data.get('fecha_nacimiento'))


class InstitucionForm(forms.Form):
    nombre = forms.CharField(
        max_length=200,
        label='Nombre de la institución',
        error_messages={
            'required': 'El nombre de la institución es obligatorio.',
            'max_length': 'El nombre no puede superar los 200 caracteres.',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre completo de la institución',
        })
    )
    email = forms.CharField(
        required=False,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'contacto@institucion.com',
            'data-validate': 'email',
        })
    )
    telefono = forms.CharField(
        required=False,
        label='Teléfono de contacto',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Solo números, sin guiones',
            'data-validate': 'phone',
            'inputmode': 'numeric',
        })
    )
    direccion = forms.CharField(
        required=False,
        max_length=255,
        label='Dirección',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Av. Mariscal López 1234',
        })
    )
    ciudad = forms.CharField(
        required=False,
        max_length=120,
        label='Ciudad',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Asunción',
        })
    )
    imagen = forms.FileField(
        required=False,
        label='Imagen / Logo',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/png,image/jpeg,image/jpg,image/webp,image/gif',
        })
    )
    activo = forms.BooleanField(
        required=False,
        initial=True,
        label='Institución habilitada',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_email(self):
        return validar_email(self.cleaned_data.get('email', '').strip())

    def clean_telefono(self):
        return validar_telefono(self.cleaned_data.get('telefono', '').strip())

    def clean_direccion(self):
        return validar_direccion(self.cleaned_data.get('direccion', '').strip())

    def clean_ciudad(self):
        return validar_ciudad(self.cleaned_data.get('ciudad', '').strip())

    def clean_imagen(self):
        img = self.cleaned_data.get('imagen')
        if not img or not hasattr(img, 'name'):
            return img
        ext = img.name.rsplit('.', 1)[-1].lower() if '.' in img.name else ''
        if ext not in ('png', 'jpg', 'jpeg', 'webp', 'gif'):
            raise forms.ValidationError(
                'Formato no admitido. Use PNG, JPG, JPEG, WEBP o GIF.'
            )
        if img.size > 5 * 1024 * 1024:
            raise forms.ValidationError('La imagen no puede superar los 5 MB.')
        return img


class CursoForm(forms.Form):
    nombre = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    institucion = forms.ModelChoiceField(
        queryset=Institucion.objects.filter(activo=1).order_by('nombre'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='— Seleccione institución —',
        label='Institución',
        error_messages={'required': 'Debe seleccionar la institución a la que pertenece el curso.'},
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
    tarifa_estudiante = forms.CharField(
        required=False,
        label='Tarifa para estudiantes (₲)',
        widget=forms.TextInput(attrs={
            'class': 'form-control money-gs',
            'inputmode': 'numeric',
            'placeholder': '0',
            'autocomplete': 'off',
        })
    )

    def clean_tarifa_estudiante(self):
        v = (self.cleaned_data.get('tarifa_estudiante') or '').strip()
        if not v:
            return 0.0
        limpio = v.replace('.', '').replace(',', '').replace(' ', '')
        if not limpio.isdigit():
            raise forms.ValidationError('La tarifa debe ser un número entero en guaraníes.')
        return float(limpio)

    class _CondicionesField(forms.ModelMultipleChoiceField):
        """Renderiza cada checkbox con la descripción de la condición (no el nombre)."""
        def label_from_instance(self, obj):
            return obj.descripcion or obj.nombre

    condiciones = _CondicionesField(
        queryset=CondicionInscripcion.objects.filter(activo=1).order_by('nombre'),
        required=False,
        label='Condiciones de inscripción',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text='Seleccioná las condiciones que aplican a este curso.',
    )


def validar_fecha(valor):
    """Acepta DD/MM/YYYY o YYYY-MM-DD y devuelve siempre YYYY-MM-DD."""
    if not valor:
        return valor
    valor = valor.strip()
    m = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', valor)
    if m:
        d, mo, y = m.groups()
        valor = f'{y}-{mo}-{d}'
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', valor):
        raise forms.ValidationError('Formato inválido. Use DD/MM/AAAA.')
    try:
        import datetime
        datetime.date.fromisoformat(valor)
    except ValueError:
        raise forms.ValidationError('Fecha inválida.')
    return valor


class CohorteForm(forms.Form):
    nombre = forms.CharField(
        max_length=100,
        label='Nombre de la cohorte',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 2025-A'})
    )
    # Selector de institución (obligatorio; condiciona los cursos disponibles)
    institucion = forms.ModelChoiceField(
        queryset=Institucion.objects.filter(activo=1).order_by('nombre'),
        required=True,
        label='Institución',
        empty_label='— Seleccione institución —',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'sel_institucion'}),
        error_messages={'required': 'Debe seleccionar la institución.'},
    )
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.filter(activo=1).select_related('institucion'),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'sel_curso'}),
        empty_label='— Seleccione institución primero —',
        error_messages={'required': 'Debe seleccionar un curso.'}
    )
    fecha_inicio = forms.CharField(
        label='Fecha de inicio',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'DD/MM/AAAA',
            'inputmode': 'numeric',
            'maxlength': '10',
            'data-fecha': '1',
        })
    )
    fecha_fin = forms.CharField(
        label='Fecha de finalización',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'DD/MM/AAAA',
            'inputmode': 'numeric',
            'maxlength': '10',
            'data-fecha': '1',
        })
    )
    cupo_maximo = forms.IntegerField(
        min_value=1, initial=30,
        label='Cupo máximo',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    dias_clase = forms.MultipleChoiceField(
        choices=DIAS_SEMANA,
        required=False,
        label='Días de clase',
        widget=forms.CheckboxSelectMultiple()
    )
    carga_horaria_diaria = forms.FloatField(
        min_value=0, initial=0,
        label='Carga horaria diaria (horas)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'step': '0.5',
            'placeholder': 'Ej: 2.5'
        })
    )
    docente = forms.ChoiceField(
        required=False,
        label='Docente a cargo',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Docente
        docentes = (Docente.objects
                    .select_related('usuario')
                    .filter(usuario__activo=1)
                    .order_by('usuario__apellido', 'usuario__nombre'))
        self.fields['docente'].choices = (
            [('', '— Sin asignar —')] +
            [(d.id, f'{d.usuario.apellido}, {d.usuario.nombre}') for d in docentes]
        )

    def clean_fecha_inicio(self):
        return validar_fecha(self.cleaned_data.get('fecha_inicio'))

    def clean_fecha_fin(self):
        return validar_fecha(self.cleaned_data.get('fecha_fin'))

    def clean(self):
        cleaned = super().clean()
        fi = cleaned.get('fecha_inicio')
        ff = cleaned.get('fecha_fin')
        if fi and ff and ff < fi:
            self.add_error('fecha_fin', 'La fecha de fin no puede ser anterior a la de inicio.')

        # Validar que el curso elegido pertenezca a la institución seleccionada.
        institucion = cleaned.get('institucion')
        curso = cleaned.get('curso')
        if institucion and curso and curso.institucion_id != institucion.id:
            self.add_error(
                'curso',
                f'El curso "{curso.nombre}" no pertenece a la institución '
                f'"{institucion.nombre}". Seleccioná un curso de esa institución.'
            )
        return cleaned


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


### Forms eliminados — la liquidación de docentes ahora es 100% auto-calculada:
# El tesorero genera el pago desde el dashboard /pagos/docentes/ (vista
# pre-liquidación) que calcula automáticamente las horas verificadas × tarifa
# y propone el saldo a liquidar. Los formularios manuales PagoDocenteHorasForm
# y PagoDocenteMaterialesForm fueron removidos.