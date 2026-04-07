"""
Modelos Django para el Sistema de Gestion Academica
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class UsuarioManager(BaseUserManager):
    """Manager personalizado para Usuario"""
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('El usuario debe tener un nombre de usuario')
        email = self.normalize_email(email) if email else None
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'admin')
        return self.create_user(username, email, password, **extra_fields)


class Usuario(AbstractUser):
    """Modelo de usuario personalizado con roles"""
    
    class Rol(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        DOCENTE = 'docente', 'Docente'
        ESTUDIANTE = 'estudiante', 'Estudiante'
    
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.ESTUDIANTE,
        verbose_name='Rol'
    )
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefono')
    direccion = models.TextField(blank=True, null=True, verbose_name='Direccion')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creacion')
    
    objects = UsuarioManager()
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"
    
    @property
    def es_admin(self):
        return self.rol == self.Rol.ADMIN
    
    @property
    def es_docente(self):
        return self.rol == self.Rol.DOCENTE
    
    @property
    def es_estudiante(self):
        return self.rol == self.Rol.ESTUDIANTE


class Estudiante(models.Model):
    """Modelo de Estudiante vinculado a Usuario"""
    
    usuario = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='estudiante_perfil',
        null=True,
        blank=True
    )
    cedula = models.CharField(max_length=20, unique=True, verbose_name='Cedula')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    apellido = models.CharField(max_length=100, verbose_name='Apellido')
    email = models.EmailField(unique=True, verbose_name='Email')
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefono')
    direccion = models.TextField(blank=True, null=True, verbose_name='Direccion')
    fecha_nacimiento = models.DateField(blank=True, null=True, verbose_name='Fecha de Nacimiento')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    
    class Meta:
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
        ordering = ['apellido', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"


class Docente(models.Model):
    """Modelo de Docente vinculado a Usuario"""
    
    usuario = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='docente_perfil',
        null=True,
        blank=True
    )
    cedula = models.CharField(max_length=20, unique=True, verbose_name='Cedula')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    apellido = models.CharField(max_length=100, verbose_name='Apellido')
    email = models.EmailField(unique=True, verbose_name='Email')
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefono')
    especialidad = models.CharField(max_length=200, blank=True, null=True, verbose_name='Especialidad')
    tarifa_hora = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Tarifa por Hora'
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    
    class Meta:
        verbose_name = 'Docente'
        verbose_name_plural = 'Docentes'
        ordering = ['apellido', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"


class Curso(models.Model):
    """Modelo de Curso"""
    
    class Modalidad(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        VIRTUAL = 'virtual', 'Virtual'
        HIBRIDO = 'hibrido', 'Hibrido'
    
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Codigo')
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripcion')
    modalidad = models.CharField(
        max_length=20,
        choices=Modalidad.choices,
        default=Modalidad.PRESENCIAL,
        verbose_name='Modalidad'
    )
    duracion_horas = models.PositiveIntegerField(default=0, verbose_name='Duracion (horas)')
    costo = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Costo'
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creacion')
    
    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Cohorte(models.Model):
    """Modelo de Cohorte (instancia de un curso)"""
    
    class Estado(models.TextChoices):
        PLANIFICADO = 'planificado', 'Planificado'
        EN_CURSO = 'en_curso', 'En Curso'
        FINALIZADO = 'finalizado', 'Finalizado'
        CANCELADO = 'cancelado', 'Cancelado'
    
    curso = models.ForeignKey(
        Curso, 
        on_delete=models.CASCADE, 
        related_name='cohortes',
        verbose_name='Curso'
    )
    docente = models.ForeignKey(
        Docente, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='cohortes',
        verbose_name='Docente'
    )
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Codigo Cohorte')
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de Fin')
    horario = models.CharField(max_length=200, blank=True, null=True, verbose_name='Horario')
    cupo_maximo = models.PositiveIntegerField(default=30, verbose_name='Cupo Maximo')
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PLANIFICADO,
        verbose_name='Estado'
    )
    aula = models.CharField(max_length=100, blank=True, null=True, verbose_name='Aula')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creacion')
    
    class Meta:
        verbose_name = 'Cohorte'
        verbose_name_plural = 'Cohortes'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.codigo} - {self.curso.nombre}"
    
    @property
    def inscritos_count(self):
        return self.inscripciones.filter(estado='activa').count()
    
    @property
    def cupos_disponibles(self):
        return self.cupo_maximo - self.inscritos_count


class Inscripcion(models.Model):
    """Modelo de Inscripcion de estudiante a cohorte"""
    
    class Estado(models.TextChoices):
        ACTIVA = 'activa', 'Activa'
        COMPLETADA = 'completada', 'Completada'
        CANCELADA = 'cancelada', 'Cancelada'
        SUSPENDIDA = 'suspendida', 'Suspendida'
    
    estudiante = models.ForeignKey(
        Estudiante, 
        on_delete=models.CASCADE, 
        related_name='inscripciones',
        verbose_name='Estudiante'
    )
    cohorte = models.ForeignKey(
        Cohorte, 
        on_delete=models.CASCADE, 
        related_name='inscripciones',
        verbose_name='Cohorte'
    )
    fecha_inscripcion = models.DateField(auto_now_add=True, verbose_name='Fecha de Inscripcion')
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.ACTIVA,
        verbose_name='Estado'
    )
    monto_acordado = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Monto Acordado'
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    
    class Meta:
        verbose_name = 'Inscripcion'
        verbose_name_plural = 'Inscripciones'
        unique_together = ['estudiante', 'cohorte']
        ordering = ['-fecha_inscripcion']
    
    def __str__(self):
        return f"{self.estudiante} - {self.cohorte}"
    
    @property
    def monto_pagado(self):
        return self.pagos.filter(estado='verificado').aggregate(
            total=models.Sum('monto')
        )['total'] or Decimal('0.00')
    
    @property
    def saldo_pendiente(self):
        return self.monto_acordado - self.monto_pagado


class PagoEstudiante(models.Model):
    """Modelo de Pago de Estudiante"""
    
    class MetodoPago(models.TextChoices):
        EFECTIVO = 'efectivo', 'Efectivo'
        TRANSFERENCIA = 'transferencia', 'Transferencia'
        TARJETA = 'tarjeta', 'Tarjeta'
        CHEQUE = 'cheque', 'Cheque'
    
    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        VERIFICADO = 'verificado', 'Verificado'
        RECHAZADO = 'rechazado', 'Rechazado'
    
    inscripcion = models.ForeignKey(
        Inscripcion, 
        on_delete=models.CASCADE, 
        related_name='pagos',
        verbose_name='Inscripcion'
    )
    monto = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto'
    )
    fecha_pago = models.DateField(verbose_name='Fecha de Pago')
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        default=MetodoPago.EFECTIVO,
        verbose_name='Metodo de Pago'
    )
    numero_recibo = models.CharField(max_length=50, blank=True, null=True, verbose_name='Numero de Recibo')
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        verbose_name='Estado'
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    
    class Meta:
        verbose_name = 'Pago de Estudiante'
        verbose_name_plural = 'Pagos de Estudiantes'
        ordering = ['-fecha_pago']
    
    def __str__(self):
        return f"Pago {self.monto} - {self.inscripcion.estudiante}"


class PagoDocente(models.Model):
    """Modelo de Pago a Docente"""
    
    class MetodoPago(models.TextChoices):
        EFECTIVO = 'efectivo', 'Efectivo'
        TRANSFERENCIA = 'transferencia', 'Transferencia'
        CHEQUE = 'cheque', 'Cheque'
    
    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        PAGADO = 'pagado', 'Pagado'
        CANCELADO = 'cancelado', 'Cancelado'
    
    docente = models.ForeignKey(
        Docente, 
        on_delete=models.CASCADE, 
        related_name='pagos_recibidos',
        verbose_name='Docente'
    )
    cohorte = models.ForeignKey(
        Cohorte, 
        on_delete=models.CASCADE, 
        related_name='pagos_docente',
        verbose_name='Cohorte'
    )
    monto = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto'
    )
    horas_trabajadas = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Horas Trabajadas'
    )
    fecha_pago = models.DateField(verbose_name='Fecha de Pago')
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        default=MetodoPago.TRANSFERENCIA,
        verbose_name='Metodo de Pago'
    )
    numero_comprobante = models.CharField(max_length=50, blank=True, null=True, verbose_name='Numero de Comprobante')
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        verbose_name='Estado'
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    
    class Meta:
        verbose_name = 'Pago a Docente'
        verbose_name_plural = 'Pagos a Docentes'
        ordering = ['-fecha_pago']
    
    def __str__(self):
        return f"Pago {self.monto} a {self.docente}"


class Sesion(models.Model):
    """Modelo de Sesion de clase"""
    
    cohorte = models.ForeignKey(
        Cohorte, 
        on_delete=models.CASCADE, 
        related_name='sesiones',
        verbose_name='Cohorte'
    )
    numero_sesion = models.PositiveIntegerField(verbose_name='Numero de Sesion')
    fecha = models.DateField(verbose_name='Fecha')
    hora_inicio = models.TimeField(verbose_name='Hora de Inicio')
    hora_fin = models.TimeField(verbose_name='Hora de Fin')
    tema = models.CharField(max_length=300, blank=True, null=True, verbose_name='Tema')
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    
    class Meta:
        verbose_name = 'Sesion'
        verbose_name_plural = 'Sesiones'
        unique_together = ['cohorte', 'numero_sesion']
        ordering = ['cohorte', 'numero_sesion']
    
    def __str__(self):
        return f"Sesion {self.numero_sesion} - {self.cohorte}"


class Asistencia(models.Model):
    """Modelo de Asistencia"""
    
    class Estado(models.TextChoices):
        PRESENTE = 'presente', 'Presente'
        AUSENTE = 'ausente', 'Ausente'
        TARDANZA = 'tardanza', 'Tardanza'
        JUSTIFICADO = 'justificado', 'Justificado'
    
    sesion = models.ForeignKey(
        Sesion, 
        on_delete=models.CASCADE, 
        related_name='asistencias',
        verbose_name='Sesion'
    )
    estudiante = models.ForeignKey(
        Estudiante, 
        on_delete=models.CASCADE, 
        related_name='asistencias',
        verbose_name='Estudiante'
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.AUSENTE,
        verbose_name='Estado'
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    
    class Meta:
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        unique_together = ['sesion', 'estudiante']
        ordering = ['sesion', 'estudiante__apellido']
    
    def __str__(self):
        return f"{self.estudiante} - {self.sesion} - {self.get_estado_display()}"
